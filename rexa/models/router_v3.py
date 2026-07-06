from __future__ import annotations

import json
import time
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from rexa.infra.chat_logging import LayerMetrics, extract_token_usage
from rexa.infra.llm_failover import build_chat_model, run_with_failover, with_cached_leading_system_messages
from rexa.infra.logger import setup_logger, log_latency, log_llm_text
from rexa.models.preprocess import PreprocessResult
from rexa.prompts import ROUTER_SYSTEM_PROMPT
from rexa.tools import (
    generic_real_estate_qa,
    get_area_transaction_stats,
    get_building_price,
    get_building_registry,
    get_land_price,
    get_land_price_trend,
    get_suhan_property,
    get_suhan_rent_property,
    get_transaction_history,
    search_commercial_area,
)

load_dotenv()

log = setup_logger()

_TOOLS = [
    search_commercial_area,
    get_building_registry,
    get_land_price,
    get_transaction_history,
    get_building_price,
    get_suhan_property,
    get_suhan_rent_property,
    get_land_price_trend,
    get_area_transaction_stats,
    generic_real_estate_qa,
]

_TOOL_MAP = {tool.name: tool for tool in _TOOLS}


def _build_input_prompt(preprocess_result: PreprocessResult) -> str:
    addresses_json = json.dumps(
        [addr.model_dump() for addr in preprocess_result.addresses],
        ensure_ascii=False,
        indent=2,
    )
    prompt = f"""사용자 질문: {preprocess_result.origin}

query_type: {preprocess_result.query_type}
reason: {preprocess_result.reason}

전처리된 주소 정보:
{addresses_json}
"""
    if preprocess_result.commercial_areas:
        ca_info = [
            {"canonical": c.keyword, "sigungu_name": c.sigungu_name, "sigungu_code": c.sigungu_code}
            for c in preprocess_result.commercial_areas
        ]
        ca_json = json.dumps(ca_info, ensure_ascii=False, indent=2)
        prompt += f"\n상권 alias 매칭 결과 (search_commercial_area sigungu_code 참고):\n{ca_json}\n"
    return prompt


def _bind_router_tools(model: Any) -> Any:
    try:
        return model.bind_tools(_TOOLS, tool_choice="any")
    except TypeError:
        return model.bind_tools(_TOOLS)


def _invoke_planner_with_failover(
    messages: list[Any],
    *,
    profile: str = "fast",
) -> tuple[Any, str, str]:
    def invoke_for_provider(provider: str) -> Any:
        model = build_chat_model(provider, profile, temperature=0)
        tool_bound_model = _bind_router_tools(model)
        return tool_bound_model.invoke(with_cached_leading_system_messages(provider, messages))

    return run_with_failover(
        "router_v3_tool_calls",
        log,
        primary_call=lambda: invoke_for_provider("claude"),
        fallback_call=lambda: invoke_for_provider("openai"),
        tertiary_call=lambda: invoke_for_provider("gemini"),
        primary_provider="claude",
        fallback_provider="openai",
        tertiary_provider="gemini",
        model_profile=profile,
        include_provider_details=True,
    )


def _extract_tool_calls(message: Any) -> list[dict[str, Any]]:
    tool_calls = getattr(message, "tool_calls", None) or []
    normalized_calls: list[dict[str, Any]] = []
    for tool_call in tool_calls:
        name = tool_call.get("name")
        if name not in _TOOL_MAP:
            continue
        args = tool_call.get("args") or {}
        if not isinstance(args, dict):
            continue
        normalized_calls.append({"name": name, "args": args})
    return normalized_calls


def _invoke_tool(name: str, args: dict[str, Any]) -> dict:
    tool = _TOOL_MAP[name]
    payload = {key: value for key, value in args.items() if value is not None}
    log.info(f"[라우터V3] 툴 호출 ▶ {name}({payload})")
    result = tool.invoke(payload)
    # DTO 인스턴스는 __str__ → JSON → dict 변환 (answer.py가 dict로 접근)
    if not isinstance(result, dict):
        result = json.loads(str(result))
    return result


def retrieve_with_metrics(preprocess_result: PreprocessResult) -> tuple[dict, LayerMetrics]:
    started_at = time.perf_counter()
    timing_breakdown: dict[str, int] = {}
    addr_count = len(preprocess_result.addresses)
    log.info(
        f"[라우터V3] 시작 ▶ 질문: {preprocess_result.origin!r} | "
        f"query_type={preprocess_result.query_type} | 주소 {addr_count}개"
    )

    if preprocess_result.query_type == "D":
        log.info("[라우터V3] D 타입 → 툴 호출 생략")
        payload = {
            "origin": preprocess_result.origin,
            "query_type": preprocess_result.query_type,
            "route": preprocess_result.route,
            "reason": preprocess_result.reason,
            "decision_code": preprocess_result.decision_code,
            "response_mode": preprocess_result.response_mode,
            "template_code": preprocess_result.template_code,
            "risk_flags": preprocess_result.risk_flags,
            "addresses": [addr.model_dump() for addr in preprocess_result.addresses],
            "retrieval": {},
        }
        metrics = LayerMetrics(
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            timing_breakdown=timing_breakdown,
        )
        log_latency(log, "[라우터V3]", metrics.timing_payload())
        return payload, metrics

    step_started_at = time.perf_counter()
    input_prompt = _build_input_prompt(preprocess_result)
    timing_breakdown["input_prompt_build_ms"] = int((time.perf_counter() - step_started_at) * 1000)
    log_llm_text(log, "[라우터V3]", "->", input_prompt)
    step_started_at = time.perf_counter()
    planner_message, provider, model_name = _invoke_planner_with_failover(
        [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=input_prompt),
        ],
        profile="fast",
    )
    timing_breakdown["planner_llm_ms"] = int((time.perf_counter() - step_started_at) * 1000)


    tool_calls = _extract_tool_calls(planner_message)
    timing_breakdown["tool_call_count"] = len(tool_calls)
    log.info(f"planner_ message: {tool_calls}")
    log_llm_text(log, "[라우터V3]", " tool_calls ", json.dumps(tool_calls, ensure_ascii=False, indent=2))

    tool_results: dict[str, list[Any]] = {}
    tool_timing: dict[str, int] = {}
    total_tool_ms = 0
    for tool_call in tool_calls:
        step_started_at = time.perf_counter()
        result = _invoke_tool(tool_call["name"], tool_call["args"])
        elapsed_ms = int((time.perf_counter() - step_started_at) * 1000)
        total_tool_ms += elapsed_ms
        tool_name = tool_call["name"]
        tool_timing[tool_name] = tool_timing.get(tool_name, 0) + elapsed_ms
        tool_results.setdefault(tool_call["name"], []).append(result)
    timing_breakdown["tool_invoke_ms"] = total_tool_ms
    for tool_name, elapsed_ms in tool_timing.items():
        timing_breakdown[f"tool:{tool_name}_ms"] = elapsed_ms

    called = {name: len(values) for name, values in tool_results.items()}
    log.info(f"[라우터V3] 완료 ◀ 총 {sum(called.values())}회 호출 | {called}")

    payload = {
        "origin": preprocess_result.origin,
        "query_type": preprocess_result.query_type,
        "route": preprocess_result.route,
        "reason": preprocess_result.reason,
        "decision_code": preprocess_result.decision_code,
        "response_mode": preprocess_result.response_mode,
        "template_code": preprocess_result.template_code,
        "risk_flags": preprocess_result.risk_flags,
        "addresses": [addr.model_dump() for addr in preprocess_result.addresses],
        "retrieval": tool_results,
    }
    metrics = LayerMetrics(
        provider=provider,
        model_name=model_name,
        latency_ms=int((time.perf_counter() - started_at) * 1000),
        tokens=extract_token_usage(planner_message),
        timing_breakdown=timing_breakdown,
    )
    log_latency(log, "[라우터V3]", metrics.timing_payload())
    return payload, metrics


def retrieve(preprocess_result: PreprocessResult) -> dict:
    payload, _ = retrieve_with_metrics(preprocess_result)
    return payload
