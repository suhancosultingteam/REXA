from __future__ import annotations

import json
import time
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from rexa.infra.chat_logging import LayerMetrics, extract_token_usage
from rexa.infra.llm_failover import build_chat_model, run_with_failover, with_cached_leading_system_messages
from rexa.infra.logger import setup_logger, log_llm_text
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

_ROUTER_V3_SYSTEM_PROMPT = """
당신은 부동산 데이터 조회 라우터입니다.

역할:
- 사용자 질문과 전처리된 주소 정보를 보고 필요한 툴 호출만 계획하세요.
- 질문에 답하지 마세요.
- 조회 결과를 요약하지 마세요.
- 자연어 응답 대신 tool_calls 만 생성하세요.

규칙:
- query_type을 반드시 참고하세요.
- 필요한 툴만 호출하세요.
- 여러 툴이 필요하면 모두 호출 계획에 넣으세요.
- 주소 정보가 여러 개면 각 주소를 별도 대상으로 판단하세요.
- 전처리된 주소 정보에 포함된 sigungu_code, bjdong_code, bun, ji, lat, lng 값을 그대로 사용하세요.
- 매물/임대 면적 관련 툴 인자는 모두 ㎡ 기준입니다.
- 사용자가 평(예: 100평, 30평)으로 면적을 말하면 반드시 ㎡로 환산해서 넣으세요. 1평 = 3.3058㎡ 입니다.
- 예: 100평 이내 -> max=330.58, 30평 이상 -> min=99.174
- 충분한 정보가 없어서 조회할 수 없는 툴은 호출하지 마세요.
- D 타입이면 tool_calls 를 만들지 마세요.
- B 타입도 필요하면 generic_real_estate_qa 외 다른 부동산 툴을 함께 사용할 수 있습니다.
- 조회 없이 답할 수 있는 일반 개념 질문에는 generic_real_estate_qa 를 우선 고려하세요.
- 특정 건물의 가격 판단이나 매입 적정성 질문이면 get_building_price를 우선 사용하세요.
- get_transaction_history는 실거래가, 최근 거래 사례, 매매 이력, 마지막 거래 시점/가격처럼 거래 자체를 직접 묻는 경우에만 사용하세요.
- 단순 가격 추정, 건물 소개, 입지 평가, 투자 의견 질문에는 거래 질문이 명시되지 않으면 get_transaction_history를 호출하지 마세요.
- 상권, 유동인구, 업종 분포, 생존률, 입지 평가 질문이면 search_commercial_area 를 고려하세요.
- get_suhan_property 와 get_suhan_rent_property 는 서안개발 자체 매물 툴이며 용도가 다릅니다:
  - get_suhan_property: 매매 매물. "매물", "부지", "건물 살 수 있어?", "매입" 등 매매 문의, 또는 임대 맥락이 없는 단순 매물 문의일 때.
  - get_suhan_rent_property: 임대 매물. "임대", "임차", "월세", "전세", "빌릴 수 있는 공간" 같은 임대 표현이 있거나, "오피스", "사무실", "업무공간", "사옥", "office"처럼 통상 임대 탐색으로 해석되는 표현일 때 우선 사용.
  - "오피스 찾아줘", "사무실 구해줘", "업무공간 알아봐줘"처럼 매매 언급 없는 오피스성 공간 탐색은 기본적으로 임대 요청으로 해석하세요.
  - 두 툴을 동시에 호출하지 마세요. 매매·임대 구분이 없더라도 오피스/사무실 계열은 get_suhan_rent_property 를 우선 사용하고, 그 외 중립적인 "매물 찾아줘"만 get_suhan_property(매매) 기본값으로 처리하세요.
""".strip()


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
        )
        return payload, metrics

    input_prompt = _build_input_prompt(preprocess_result)
    log_llm_text(log, "[라우터V3]", "->", input_prompt)
    planner_message, provider, model_name = _invoke_planner_with_failover(
        [
            SystemMessage(content=_ROUTER_V3_SYSTEM_PROMPT),
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=input_prompt),
        ],
        profile="fast",
    )


    tool_calls = _extract_tool_calls(planner_message)
    log.info(f"planner_ message: {tool_calls}")
    log_llm_text(log, "[라우터V3]", " tool_calls ", json.dumps(tool_calls, ensure_ascii=False, indent=2))

    tool_results: dict[str, list[Any]] = {}
    for tool_call in tool_calls:
        result = _invoke_tool(tool_call["name"], tool_call["args"])
        tool_results.setdefault(tool_call["name"], []).append(result)

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
    )
    return payload, metrics


def retrieve(preprocess_result: PreprocessResult) -> dict:
    payload, _ = retrieve_with_metrics(preprocess_result)
    return payload
