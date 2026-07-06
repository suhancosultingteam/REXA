import re
import time

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from rexa.infra.chat_logging import LayerMetrics, extract_token_usage
from rexa.infra.llm_failover import build_chat_model, run_with_failover, with_cached_leading_system_messages
from rexa.infra.logger import setup_logger, log_latency, log_messages
from rexa.models.answer_v2.building_price_template import try_build_building_price_answer
from rexa.models.answer_v2.context_builder import build_answer_context
from rexa.prompts import (
    ANSWER_PROMPT_A,
    ANSWER_PROMPT_B,
    ANSWER_PROMPT_C,
    ANSWER_PROMPT_D,
    BASE_ANSWER_SYSTEM_PROMPT,
)

load_dotenv()

log = setup_logger()

_SYSTEM_PROMPT = BASE_ANSWER_SYSTEM_PROMPT

_SERVICE_GUIDE_MESSAGE = (
    "주소나 장소가 확인되면 건물 정보, 공시지가, 실거래가, 상권 분석, 추정가 같은 데이터는 이어서 바로 확인해드릴 수 있어요."
)

_SEOUL_ONLY_TOOLS = {"get_building_registry", "get_building_price", "search_commercial_area"}
SEOUL_ONLY_NOTICE = "렉사는 현재 서울 지역 분석만 지원합니다."


def _is_seoul_sigungu_code(sigungu_code: str) -> bool:
    return sigungu_code.startswith("11") and len(sigungu_code) == 5


def _needs_seoul_only_notice(retrieval_result: dict, retrieval: dict) -> bool:
    if not any(tool_name in retrieval for tool_name in _SEOUL_ONLY_TOOLS):
        return False
    addresses = retrieval_result.get("addresses") or []
    sigungu_codes = [str(addr.get("sigungu_code") or "") for addr in addresses if addr.get("sigungu_code")]
    if not sigungu_codes:
        return False
    return not any(_is_seoul_sigungu_code(code) for code in sigungu_codes)

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]",
    flags=re.UNICODE,
)


def _resolve_query_type(retrieval_result: dict) -> str:
    query_type = str(retrieval_result.get("query_type") or "").strip().upper()
    if query_type in {"A", "B", "C", "D"}:
        return query_type

    decision_code = str(retrieval_result.get("decision_code") or "").strip().upper()
    if decision_code == "ALLOW_DOMAIN":
        return "A"
    if decision_code == "ALLOW_FALLBACK":
        return "B"
    if decision_code in {"LIMITED_GUIDE", "LIMITED_CAUTION", "HANDOFF_HUMAN"}:
        return "C"
    if decision_code == "REFUSE_POLICY":
        return "D"
    return "A"


def _get_type_prompt(query_type: str) -> str:
    prompt_map = {
        "A": ANSWER_PROMPT_A,
        "B": ANSWER_PROMPT_B,
        "C": ANSWER_PROMPT_C,
        "D": ANSWER_PROMPT_D,
    }
    return prompt_map.get(query_type, ANSWER_PROMPT_A)


def _strip_markdown(text: str) -> str:
    cleaned = text.replace("**", "").replace("`", "")
    cleaned = cleaned.replace("### ", "").replace("## ", "").replace("# ", "")
    lines = []
    for line in cleaned.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("- "):
            prefix_len = len(line) - len(stripped)
            line = f"{line[:prefix_len]}{stripped[2:]}"
        lines.append(line)
    return "\n".join(lines).strip()


def _strip_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text)


def generate_answer_with_metrics(
    retrieval_result: dict,
    history: list[dict] | None = None,
) -> tuple[str, LayerMetrics]:
    started_at = time.perf_counter()
    timing_breakdown: dict[str, int] = {}
    origin = retrieval_result["origin"]
    query_type = _resolve_query_type(retrieval_result)
    retrieval = retrieval_result.get("retrieval", {})
    type_system_prompt = _get_type_prompt(query_type)

    log.info(f"[결과V2] 시작 ▶ 질문: {origin!r} | query_type={query_type}")
    log.debug(f"[결과V2] 조회된 툴: {list(retrieval.keys())}")

    needs_seoul_only_notice = _needs_seoul_only_notice(retrieval_result, retrieval)

    if not retrieval and query_type != 'D':
        log.info("[결과V2] 툴 미호출 → fallback 응답")
        answer_text = (
            "지금 질문만으로는 조회할 위치를 정확히 잡기 어려워요. "
            "예를 들면 `역삼1동`, `강남역`, `테헤란로 123`처럼 장소나 주소를 같이 보내주시면 바로 확인해볼게요.\n\n"
            f"{_SERVICE_GUIDE_MESSAGE}"
        )
        metrics = LayerMetrics(
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            timing_breakdown={"fallback_response_ms": int((time.perf_counter() - started_at) * 1000)},
        )
        log_latency(log, "[결과V2]", metrics.timing_payload())
        return answer_text, metrics

    if query_type == "A" and retrieval.get("get_building_price"):
        template_answer = try_build_building_price_answer(origin, retrieval)
        if template_answer is not None:
            log.info("[결과V2] 건물가격 템플릿 응답 사용")
            if needs_seoul_only_notice:
                template_answer = f"{template_answer}\n\n{SEOUL_ONLY_NOTICE}"
            metrics = LayerMetrics(
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                timing_breakdown={"building_price_template_ms": int((time.perf_counter() - started_at) * 1000)},
            )
            log_latency(log, "[결과V2]", metrics.timing_payload())
            return template_answer, metrics

    step_started_at = time.perf_counter()
    context = build_answer_context(retrieval)
    timing_breakdown["context_build_ms"] = int((time.perf_counter() - step_started_at) * 1000)
    log.debug(f"[결과V2] retrieval 컨텍스트 사용 ({len(context)}자)")

    has_suhan = any(
        tool_name in retrieval and any(
            isinstance(r, dict) and "error" not in r
            for r in retrieval[tool_name]
        )
        for tool_name in {"get_suhan_property", "get_suhan_rent_property"}
    )
    suhan_reminder = (
        "\n\n주의: 매물 데이터는 카카오 itemCard로 별도 표시됩니다. "
        "본문 텍스트에서는 매물 목록을 장황하게 반복하지 말고, 전체 결과 요약과 차이점, 참고 포인트만 간결하게 설명하세요."
        if has_suhan else ""
    )

    messages: list = [
        SystemMessage(content=_SYSTEM_PROMPT),
        SystemMessage(content=type_system_prompt),
    ]
    step_started_at = time.perf_counter()
    for msg in (history or []):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(
        HumanMessage(
            content=(
                f"사용자 질문: {origin}\n\n"
                f"조회된 데이터:\n{context}\n\n"
                f"위 데이터를 근거로 카카오톡 챗봇처럼 자연스럽게, "
                f"하지만 이유와 근거가 충분히 드러나도록 답변해 주세요.{suhan_reminder}"
            )
        )
    )
    timing_breakdown["message_build_ms"] = int((time.perf_counter() - step_started_at) * 1000)

    log.debug("[결과V2] LLM 호출 중 (claude 우선, openai failover)")
    log_messages(log, messages, "[결과V2]")
    step_started_at = time.perf_counter()
    llm_response, provider, model_name = run_with_failover(
        "answer_v2_chat",
        log,
        primary_call=lambda: build_chat_model("claude", "quality", temperature=0.3).invoke(
            with_cached_leading_system_messages("claude", messages)
        ),
        fallback_call=lambda: build_chat_model("openai", "quality", temperature=0.3).invoke(
            with_cached_leading_system_messages("openai", messages)
        ),
        tertiary_call=lambda: build_chat_model("gemini", "quality", temperature=0.3).invoke(
            with_cached_leading_system_messages("gemini", messages)
        ),
        model_profile="quality",
        include_provider_details=True,
    )
    timing_breakdown["llm_ms"] = int((time.perf_counter() - step_started_at) * 1000)
    response = llm_response
    log_messages(log, [response], "[결과V2]")
    step_started_at = time.perf_counter()
    answer_text = _strip_emojis(_strip_markdown(response.content))
    if needs_seoul_only_notice:
        answer_text = f"{answer_text}\n\n{SEOUL_ONLY_NOTICE}"
    timing_breakdown["postprocess_ms"] = int((time.perf_counter() - step_started_at) * 1000)

    log.info(f"[결과V2] 완료 ◀ 답변 {len(answer_text)}자 생성")
    log.debug(f"[결과V2] 답변 내용:\n{answer_text}")

    metrics = LayerMetrics(
        provider=provider,
        model_name=model_name,
        latency_ms=int((time.perf_counter() - started_at) * 1000),
        tokens=extract_token_usage(response),
        timing_breakdown=timing_breakdown,
    )
    log_latency(log, "[결과V2]", metrics.timing_payload())
    return answer_text, metrics


def generate_answer(
    retrieval_result: dict,
    history: list[dict] | None = None,
) -> str:
    answer_text, _ = generate_answer_with_metrics(retrieval_result, history=history)
    return answer_text
