import json
import logging
import sys
from datetime import datetime
from typing import Any

from rexa.infra.chat_logging import merge_token_usage


_NOISY_LOGGERS = (
    "__main__",
    "werkzeug",
    "httpx",
    "httpcore",
    "anthropic",
)


def _json_safe(obj):
    try:
        json.dumps(obj, ensure_ascii=False)
        return obj
    except (TypeError, ValueError):
        return str(obj)


class PipelineFormatter(logging.Formatter):
    LEVEL_COLORS = {
        "DEBUG":    "\033[90m",   # 회색
        "INFO":     "\033[0m",    # 기본
        "WARNING":  "\033[33m",   # 노랑
        "ERROR":    "\033[31m",   # 빨강
        "CRITICAL": "\033[35m",   # 보라
    }
    STAGE_COLORS = {
        "[파이프라인]": "\033[97m",   # 밝은 흰색
        "[전처리]":    "\033[36m",   # 청록
        "[라우터]":    "\033[35m",   # 보라
        "[툴]":        "\033[32m",   # 초록
        "[LLM]":       "\033[34m",   # 파랑
        "[LLM->]":     "\033[31m",   # 빨강
        "[LLM<-]":     "\033[31m",   # 빨강
        "[결과]":      "\033[33m",   # 노랑
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        level_color = self.LEVEL_COLORS.get(record.levelname, "")

        msg = record.getMessage()

        stage_color = ""
        for tag, color in self.STAGE_COLORS.items():
            if msg.startswith(tag):
                stage_color = color
                break

        color = stage_color or level_color
        return f"{self.RESET}\033[90m{ts}\033[0m  {color}{msg}{self.RESET}"


def _suppress_noisy_loggers() -> None:
    for name in _NOISY_LOGGERS:
        noisy_logger = logging.getLogger(name)
        noisy_logger.handlers.clear()
        noisy_logger.propagate = False
        noisy_logger.setLevel(logging.WARNING)
        noisy_logger.disabled = True


def setup_logger(name: str = "rexa", level: int = logging.DEBUG) -> logging.Logger:
    _suppress_noisy_loggers()

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(PipelineFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_messages(logger: logging.Logger, messages: list, stage: str) -> None:
    """LangChain 메시지 체인을 단계별로 로깅합니다."""
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__

        if msg_type in ("SystemMessage", "HumanMessage"):
            logger.info(f"[LLM->] {stage} [{msg_type}] {msg.content}")

        elif msg_type == "AIMessage":
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    args_str = json.dumps(tc.get("args", {}), ensure_ascii=False)
                    logger.info(f"[LLM<-] {stage} [AIMessage] 툴 호출 결정: {tc['name']}({args_str})")
            else:
                content = msg.content
                if content:
                    logger.info(f"[LLM<-] {stage} [AIMessage] {content}")

        elif hasattr(msg, "name") and msg.name:
            try:
                parsed = json.loads(msg.content)
                has_error = "error" in parsed
                count_info = ""
                for key in ("count", "buildings", "transactions", "chunks"):
                    if key in parsed:
                        val = parsed[key]
                        count_info = f" | {key}={len(val) if isinstance(val, list) else val}"
                        break
                status = "ERROR" if has_error else "OK"
                logger.info(f"{stage} [툴] {msg.name} → {status}{count_info}")
                if has_error:
                    logger.warning(f"{stage} [툴] {msg.name} 오류: {parsed.get('error')}")
                else:
                    logger.debug(f"{stage} [툴] {msg.name} 상세:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}")
            except (json.JSONDecodeError, TypeError):
                logger.info(f"{stage} [툴] {msg.name} → {msg.content}")


def log_llm_text(logger: logging.Logger, stage: str, direction: str, text: str) -> None:
    logger.info(f"[LLM{direction}] {stage} {text}")


def log_latency(logger: logging.Logger, stage: str, timings: dict[str, int]) -> None:
    if not timings:
        return
    payload = " ".join(f"{key}={value}ms" if key.endswith("_ms") or key == "total_ms" else f"{key}={value}" for key, value in timings.items())
    logger.info(f"[LATENCY] {stage} {payload}")


def _iter_stream_chunk_messages(payload: Any) -> list[tuple[str, list]]:
    if not isinstance(payload, dict):
        return []

    node_messages: list[tuple[str, list]] = []
    for node_name, node_payload in payload.items():
        if isinstance(node_payload, dict) and isinstance(node_payload.get("messages"), list):
            node_messages.append((node_name, node_payload["messages"]))
    return node_messages


def invoke_agent_with_logging(agent: Any, payload: dict, logger: logging.Logger, stage: str) -> tuple[dict, Any]:
    model_calls = 0
    tool_steps = 0
    latest: dict | None = None
    usage_messages: list[Any] = []

    for chunk in agent.stream(payload, stream_mode=["updates", "values"]):
        if not isinstance(chunk, tuple) or len(chunk) != 2:
            continue

        mode, chunk_payload = chunk

        if mode == "updates":
            for node_name, messages in _iter_stream_chunk_messages(chunk_payload):
                if node_name == "model":
                    model_calls += 1
                    logger.info(f"{stage} [AGENT] model step #{model_calls}")
                    usage_messages.extend(messages)
                elif node_name == "tools":
                    tool_steps += 1
                    logger.info(f"{stage} [AGENT] tool step #{tool_steps}")
                else:
                    logger.info(f"{stage} [AGENT] node={node_name}")
                log_messages(logger, messages, stage)
        elif mode == "values":
            latest = chunk_payload

    logger.info(f"{stage} [AGENT] 완료 | model_steps={model_calls} tool_steps={tool_steps}")

    if latest is None:
        msg = f"{stage} agent stream did not return final state"
        raise RuntimeError(msg)

    return latest, merge_token_usage(usage_messages)
