import logging
import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Literal, TypeVar, overload

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI


T = TypeVar("T")

_DEFAULT_PRIMARY_PROVIDER = os.getenv("LLM_PRIMARY_PROVIDER", "claude").strip().lower() or "claude"
_DEFAULT_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "openai").strip().lower() or "openai"
_DEFAULT_TERTIARY_PROVIDER = os.getenv("LLM_TERTIARY_PROVIDER", "gemini").strip().lower() or "gemini"
_FAILOVER_ENABLED = os.getenv("LLM_FAILOVER_ENABLED", "1").strip().lower() not in {"0", "false", "off", "no"}

_CLAUDE_FAST_MODEL = os.getenv("ANTHROPIC_FAST_MODEL", "claude-haiku-4-5-20251001")
_CLAUDE_QUALITY_MODEL = os.getenv("ANTHROPIC_QUALITY_MODEL", "claude-sonnet-4-6")
_OPENAI_FAST_MODEL = os.getenv("OPENAI_FAST_MODEL", "gpt-4o-mini")
_OPENAI_QUALITY_MODEL = os.getenv("OPENAI_QUALITY_MODEL", "gpt-4o")
_GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")
_GEMINI_QUALITY_MODEL = os.getenv("GEMINI_QUALITY_MODEL", "gemini-2.5-pro")


def model_name_for(provider: str, profile: str) -> str:
    normalized_provider = provider.strip().lower()
    normalized_profile = profile.strip().lower()

    if normalized_provider == "claude":
        return _CLAUDE_QUALITY_MODEL if normalized_profile == "quality" else _CLAUDE_FAST_MODEL
    if normalized_provider == "openai":
        return _OPENAI_QUALITY_MODEL if normalized_profile == "quality" else _OPENAI_FAST_MODEL
    if normalized_provider == "gemini":
        return _GEMINI_QUALITY_MODEL if normalized_profile == "quality" else _GEMINI_FAST_MODEL
    raise ValueError(f"unsupported provider: {provider}")


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    opened_at: float = 0.0
    state: str = "closed"


class CircuitBreakerRegistry:
    def __init__(self, failure_threshold: int = 2, recovery_timeout_seconds: int = 120):
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_timeout_seconds = max(1, recovery_timeout_seconds)
        self._states: dict[str, CircuitBreakerState] = {}
        self._lock = Lock()

    def _now(self) -> float:
        return time.monotonic()

    def _get_state(self, key: str) -> CircuitBreakerState:
        state = self._states.get(key)
        if state is None:
            state = CircuitBreakerState()
            self._states[key] = state
        return state

    def allow_request(self, key: str) -> bool:
        with self._lock:
            state = self._get_state(key)
            if state.state != "open":
                return True

            if self._now() - state.opened_at >= self.recovery_timeout_seconds:
                state.state = "half_open"
                return True

            return False

    def record_success(self, key: str) -> None:
        with self._lock:
            self._states[key] = CircuitBreakerState()

    def record_failure(self, key: str) -> None:
        with self._lock:
            state = self._get_state(key)
            state.failure_count += 1
            if state.state == "half_open" or state.failure_count >= self.failure_threshold:
                state.state = "open"
                state.opened_at = self._now()

    def snapshot(self, key: str) -> CircuitBreakerState:
        with self._lock:
            state = self._get_state(key)
            return CircuitBreakerState(
                failure_count=state.failure_count,
                opened_at=state.opened_at,
                state=state.state,
            )


_BREAKER_REGISTRY = CircuitBreakerRegistry(
    failure_threshold=int(os.getenv("LLM_BREAKER_FAILURE_THRESHOLD", "2")),
    recovery_timeout_seconds=int(os.getenv("LLM_BREAKER_RECOVERY_SECONDS", "120")),
)


def _provider_api_key(provider: str) -> str:
    if provider == "claude":
        return os.getenv("ANTHROPIC_API_KEY", "").strip()
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY", "").strip()
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")).strip()
    return ""


def provider_is_available(provider: str) -> bool:
    if not _provider_api_key(provider):
        return False
    if provider != "gemini":
        return True
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: F401
    except ImportError:
        return False
    return True


def build_chat_model(provider: str, profile: str, temperature: float = 0) -> Any:
    normalized_provider = provider.strip().lower()

    if normalized_provider == "claude":
        model = model_name_for("claude", profile)
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=_provider_api_key("claude"),
        )

    if normalized_provider == "openai":
        model = model_name_for("openai", profile)
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=_provider_api_key("openai"),
        )

    if normalized_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = model_name_for("gemini", profile)
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=_provider_api_key("gemini"),
        )

    raise ValueError(f"unsupported provider: {provider}")


def build_cached_system_message(provider: str, text: str) -> SystemMessage:
    """provider별 정적 system prompt 캐싱.

    claude: Anthropic prompt caching (cache_control ephemeral) 명시 적용.
    openai: 서버가 prefix 자동 캐싱하므로 plain text 그대로.
    gemini: 별도 CachedContent API 필요, 현재 미구현 (no-op).
    """
    if provider.strip().lower() == "claude":
        return SystemMessage(
            content=[{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
        )
    return SystemMessage(content=text)


def with_cached_leading_system_messages(provider: str, messages: list[Any]) -> list[Any]:
    """선두 SystemMessage(들)을 provider별 캐싱 적용 버전으로 교체.

    static system prompt가 항상 메시지 리스트 앞쪽에 오는 현재 호출부 패턴 전제.
    plain string content인 SystemMessage만 교체 대상으로 삼는다 (이미 구조화된 content는 건드리지 않음).
    """
    rebuilt: list[Any] = []
    for message in messages:
        if isinstance(message, SystemMessage) and isinstance(message.content, str):
            rebuilt.append(build_cached_system_message(provider, message.content))
        else:
            rebuilt.append(message)
    return rebuilt


def invoke_structured_with_failover(
    operation_key: str,
    logger: logging.Logger,
    schema: type[Any],
    messages: list[Any],
    *,
    profile: str = "fast",
    temperature: float = 0,
    primary_provider: str = _DEFAULT_PRIMARY_PROVIDER,
    fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER,
    tertiary_provider: str = _DEFAULT_TERTIARY_PROVIDER,
    registry: CircuitBreakerRegistry = _BREAKER_REGISTRY,
) -> tuple[Any, str, str]:
    def invoke_for_provider(provider: str) -> Any:
        model = build_chat_model(provider, profile, temperature=temperature)
        try:
            structured = model.with_structured_output(schema, include_raw=True)
        except TypeError:
            structured = model.with_structured_output(schema)
        return structured.invoke(with_cached_leading_system_messages(provider, messages))

    return run_with_failover(
        operation_key,
        logger,
        primary_call=lambda: invoke_for_provider(primary_provider),
        fallback_call=lambda: invoke_for_provider(fallback_provider),
        tertiary_call=lambda: invoke_for_provider(tertiary_provider),
        primary_provider=primary_provider,
        fallback_provider=fallback_provider,
        tertiary_provider=tertiary_provider,
        model_profile=profile,
        include_provider_details=True,
        registry=registry,
    )


def invoke_agent_with_failover(
    operation_key: str,
    logger: logging.Logger,
    *,
    agent_factory: Callable[[Any], Any],
    messages_payload: dict[str, Any],
    stage: str,
    system_prompt: str,
    tools: list[Any],
    profile: str = "fast",
    temperature: float = 0,
    primary_provider: str = _DEFAULT_PRIMARY_PROVIDER,
    fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER,
    tertiary_provider: str = _DEFAULT_TERTIARY_PROVIDER,
    registry: CircuitBreakerRegistry = _BREAKER_REGISTRY,
) -> tuple[tuple[dict, Any], str, str]:
    from logger import invoke_agent_with_logging

    def invoke_for_provider(provider: str) -> tuple[dict, Any]:
        model = build_chat_model(provider, profile, temperature=temperature)
        agent = agent_factory(model=model, tools=tools, system_prompt=system_prompt)
        return invoke_agent_with_logging(agent, messages_payload, logger, stage)

    return run_with_failover(
        operation_key,
        logger,
        primary_call=lambda: invoke_for_provider(primary_provider),
        fallback_call=lambda: invoke_for_provider(fallback_provider),
        tertiary_call=lambda: invoke_for_provider(tertiary_provider),
        primary_provider=primary_provider,
        fallback_provider=fallback_provider,
        tertiary_provider=tertiary_provider,
        model_profile=profile,
        include_provider_details=True,
        registry=registry,
    )


def _run_provider_call(
    operation_key: str,
    logger: logging.Logger,
    provider_name: str,
    call: Callable[[], T],
    registry: CircuitBreakerRegistry,
) -> T:
    breaker_key = f"{provider_name}:{operation_key}"
    if not registry.allow_request(breaker_key):
        snapshot = registry.snapshot(breaker_key)
        raise RuntimeError(
            f"circuit open for provider={provider_name} operation={operation_key} state={snapshot.state}"
        )

    try:
        result = call()
    except Exception:
        registry.record_failure(breaker_key)
        raise

    registry.record_success(breaker_key)
    return result


@overload
def run_with_failover(
    operation_key: str,
    logger: logging.Logger,
    primary_call: Callable[[], T],
    fallback_call: Callable[[], T] | None = None,
    tertiary_call: Callable[[], T] | None = None,
    *,
    primary_provider: str = _DEFAULT_PRIMARY_PROVIDER,
    fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER,
    tertiary_provider: str = _DEFAULT_TERTIARY_PROVIDER,
    model_profile: str | None = None,
    include_provider_details: Literal[False] = False,
    registry: CircuitBreakerRegistry = _BREAKER_REGISTRY,
) -> T: ...


@overload
def run_with_failover(
    operation_key: str,
    logger: logging.Logger,
    primary_call: Callable[[], T],
    fallback_call: Callable[[], T] | None = None,
    tertiary_call: Callable[[], T] | None = None,
    *,
    primary_provider: str = _DEFAULT_PRIMARY_PROVIDER,
    fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER,
    tertiary_provider: str = _DEFAULT_TERTIARY_PROVIDER,
    model_profile: str,
    include_provider_details: Literal[True],
    registry: CircuitBreakerRegistry = _BREAKER_REGISTRY,
) -> tuple[T, str, str]: ...


def run_with_failover(
    operation_key: str,
    logger: logging.Logger,
    primary_call: Callable[[], T],
    fallback_call: Callable[[], T] | None = None,
    tertiary_call: Callable[[], T] | None = None,
    *,
    primary_provider: str = _DEFAULT_PRIMARY_PROVIDER,
    fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER,
    tertiary_provider: str = _DEFAULT_TERTIARY_PROVIDER,
    model_profile: str | None = None,
    include_provider_details: bool = False,
    registry: CircuitBreakerRegistry = _BREAKER_REGISTRY,
) -> T | tuple[T, str, str]:
    primary_name = primary_provider.strip().lower()
    fallback_name = fallback_provider.strip().lower()
    tertiary_name = tertiary_provider.strip().lower()

    if include_provider_details and not model_profile:
        raise ValueError("model_profile is required when include_provider_details=True")

    provider_chain: list[tuple[str, Callable[[], T]]] = [(primary_name, primary_call)]
    if _FAILOVER_ENABLED and fallback_call is not None and provider_is_available(fallback_name):
        provider_chain.append((fallback_name, fallback_call))
    if _FAILOVER_ENABLED and tertiary_call is not None and provider_is_available(tertiary_name):
        provider_chain.append((tertiary_name, tertiary_call))

    last_error: Exception | None = None
    for index, (provider_name, call) in enumerate(provider_chain):
        try:
            if index > 0:
                logger.warning(
                    f"[LLM] failover attempt | operation={operation_key} | provider={provider_name} | attempt={index + 1}"
                )
            result = _run_provider_call(operation_key, logger, provider_name, call, registry)
            if include_provider_details:
                return result, provider_name, model_name_for(provider_name, model_profile)
            return result
        except Exception as exc:
            snapshot = registry.snapshot(f"{provider_name}:{operation_key}")
            logger.error(
                f"[LLM] provider failed | operation={operation_key} | provider={provider_name} | "
                f"state={snapshot.state} failures={snapshot.failure_count} | {exc}"
            )
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    return primary_call()
