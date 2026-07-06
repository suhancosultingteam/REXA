import json
from collections import defaultdict, deque

from rexa.tools._utils import format_human_krw

_TOOL_LABELS = {
    "search_commercial_area": "상권 분석",
    "get_building_registry": "건축물대장",
    "get_land_price": "공시지가",
    "get_transaction_history": "실거래가",
    "get_building_price": "건물 예상 가격",
    "get_suhan_property": "서안개발 매물",
    "get_land_price_trend": "공시지가 추이",
    "get_area_transaction_stats": "주변 거래 통계",
    "generic_real_estate_qa": "일반 부동산 설명",
}

_ANSWER_EXCLUDED_TOOLS: set[str] = set()
_MAX_CONTEXT_CHARS = 10000
_MAX_ITEMS_PER_SECTION = 6


def _extract_money_krw(value: object) -> int | None:
    if isinstance(value, dict):
        value = value.get("krw")
    if value in (None, ""):
        return None
    return int(round(float(value)))


def _extract_money_human(value: object) -> str | None:
    if isinstance(value, dict):
        human = value.get("human")
        if human not in (None, ""):
            return str(human)
        value = value.get("krw")
    if value in (None, ""):
        return None
    return format_human_krw(value)


def _short_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _summarize_building_registry(results: list[dict]) -> str:
    buildings = []
    for result in results:
        building = result.get("building")
        if building:
            buildings.append(building)
            continue
        buildings.extend(result.get("buildings", []))

    if not buildings:
        return "조회 결과 없음"

    lines = []
    for building in buildings[:_MAX_ITEMS_PER_SECTION]:
        lines.append(_short_json({
            "건물명": building.get("bld_nm"),
            "주소": building.get("new_plat_plc") or building.get("plat_plc"),
            "용도": building.get("main_purps_cd_nm"),
            "구조": building.get("strct_cd_nm"),
            "대지면적_sqm": building.get("plat_area"),
            "연면적_sqm": building.get("tot_area"),
            "지상층수": building.get("grnd_flr_cnt"),
            "지하층수": building.get("ugrnd_flr_cnt"),
            "사용승인연도": building.get("use_apr_year"),
        }))
    return "\n".join(lines)


def _summarize_land_price(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        trend = result.get("trend", [])
        lines.append(_short_json({
            "latest": result.get("latest"),
            "recent_trend": trend[-3:],
        }))
    return "\n".join(lines) if lines else "조회 결과 없음"


def _summarize_transaction_history(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        transactions = result.get("transactions", [])
        lines.append(_short_json({
            "count": result.get("count", len(transactions)),
            "recent_transactions": [
                {
                    "deal_date": f"{tx.get('deal_year')}-{str(tx.get('deal_month') or '').zfill(2)}-{str(tx.get('deal_day') or '').zfill(2)}",
                    "deal_amount": tx.get("deal_amount"),
                    "building_use": tx.get("building_use"),
                    "building_type": tx.get("building_type"),
                    "land_area_sqm": tx.get("plottage_ar"),
                    "building_area_sqm": tx.get("building_ar"),
                    "floor": tx.get("floor"),
                    "address": tx.get("new_plat_plc") or tx.get("plat_plc") or tx.get("jibun"),
                    "distance_m": tx.get("distance_m"),
                }
                for tx in transactions[:_MAX_ITEMS_PER_SECTION]
            ],
        }))
    return "\n".join(lines) if lines else "조회 결과 없음"


def _summarize_building_price(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        tb = result.get("target_building") or {}
        final_estimated_price = result.get("final_estimated_price")
        if final_estimated_price is None:
            final_estimated_price = result.get("estimated_price")
        final_estimated_price_krw = _extract_money_krw(final_estimated_price)

        base_estimated_price = result.get("base_estimated_price")
        if base_estimated_price is None and result.get("base_estimated_price_krw") is not None:
            base_estimated_price = {
                "krw": result.get("base_estimated_price_krw"),
                "human": format_human_krw(result.get("base_estimated_price_krw")),
            }

        if final_estimated_price is None and result.get("final_estimated_price_krw") is not None:
            final_estimated_price = {
                "krw": result.get("final_estimated_price_krw"),
                "human": format_human_krw(result.get("final_estimated_price_krw")),
            }

        lines.append(_short_json({
            "target_building": {
                "name": tb.get("bld_nm"),
                "address": tb.get("new_plat_plc") or tb.get("plat_plc"),
                "use": tb.get("main_purps_cd_nm"),
                "plat_area_sqm": tb.get("plat_area"),
                "use_apr_year": tb.get("use_apr_year"),
            },
            "base_estimated_price": base_estimated_price,
            "final_estimated_price": final_estimated_price,
            "final_estimated_price_krw": final_estimated_price_krw,
            "final_estimated_price_display": _extract_money_human(final_estimated_price),
            "excluded": result.get("excluded"),
            "message": result.get("message"),
        }))
    return "\n".join(lines) if lines else "조회 결과 없음"


def _summarize_commercial_area(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        chunks = result.get("chunks", [])
        selected_chunks = _select_commercial_area_chunks(chunks, _MAX_ITEMS_PER_SECTION)
        chunk_lines = []
        for chunk in selected_chunks:
            query = chunk.get("matched_query") or "-"
            score = chunk.get("score")
            text = str(chunk.get("text") or "").strip()
            chunk_lines.append(
                "\n".join([
                    f"query: {query}",
                    f"score: {score}" if score is not None else "score: -",
                    f"text: {text}",
                ])
            )
        block = [
            f"district: {result.get('district') or '-'}",
            f"queries: {result.get('queries') or []}",
            f"count: {result.get('count', len(chunks))}",
        ]
        if chunk_lines:
            block.append("top_chunks:")
            block.extend(chunk_lines)
        lines.append("\n".join(block))
    return "\n".join(lines) if lines else "조회 결과 없음"


def _chunk_sort_key(chunk: dict) -> tuple[int, float]:
    score = chunk.get("score")
    if score is None:
        return (1, 0.0)
    try:
        return (0, -float(score))
    except (TypeError, ValueError):
        return (1, 0.0)


def _select_commercial_area_chunks(chunks: list[dict], limit: int) -> list[dict]:
    if limit <= 0:
        return []

    valid_chunks = [chunk for chunk in chunks if isinstance(chunk, dict)]
    if not valid_chunks:
        return []

    grouped: dict[str, deque[dict]] = defaultdict(deque)
    query_order: list[str] = []
    seen_queries: set[str] = set()

    for chunk in valid_chunks:
        query = str(chunk.get("matched_query") or "").strip() or "__ungrouped__"
        grouped[query].append(chunk)
        if query not in seen_queries:
            seen_queries.add(query)
            query_order.append(query)

    for query in query_order:
        sorted_chunks = sorted(grouped[query], key=_chunk_sort_key)
        grouped[query] = deque(sorted_chunks)

    selected: list[dict] = []
    while len(selected) < limit:
        progressed = False
        for query in query_order:
            if not grouped[query]:
                continue
            selected.append(grouped[query].popleft())
            progressed = True
            if len(selected) >= limit:
                break
        if not progressed:
            break
    return selected


def _summarize_area_transaction_stats(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        lines.append(_short_json({
            "query": result.get("query"),
            "transaction_count": result.get("transaction_count"),
            "stats": result.get("stats"),
            "recent_transactions": (result.get("transactions") or [])[:5],
        }))
    return "\n".join(lines) if lines else "조회 결과 없음"


def _summarize_generic_real_estate_qa(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        lines.append(_short_json({
            "question": result.get("question"),
            "answer": result.get("answer"),
            "source": result.get("source"),
        }))
    return "\n".join(lines) if lines else "조회 결과 없음"


def _summarize_suhan_property(results: list[dict]) -> str:
    blocks = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        for listing in (result.get("listings") or []):
            name = listing.get("name") or "(이름 없음)"
            code = listing.get("code") or "(코드 없음)"
            parts = [f"이름: {name} | 코드: {code}"]
            addr = listing.get("address") or {}
            if addr.get("road"):
                parts.append(f"주소: {addr['road']}")
            elif addr.get("jibun"):
                parts.append(f"주소: {addr['jibun']}")
            price = listing.get("price") or {}
            if price.get("human"):
                parts.append(f"가격: {price['human']}")
            area = listing.get("area") or {}
            if area.get("land_sqm") is not None:
                parts.append(f"대지면적: {area['land_sqm']}㎡")
            if area.get("total_sqm") is not None:
                parts.append(f"연면적: {area['total_sqm']}㎡")
            if listing.get("floors") is not None:
                parts.append(f"층수: {listing['floors']}층")
            station = listing.get("nearest_station") or {}
            if station.get("name"):
                parts.append(f"인접역: {station['name']} ({station.get('distance_m')}m)")
            blocks.append("\n".join(parts))
    return "\n\n".join(blocks) if blocks else "조회 결과 없음"


def _summarize_suhan_rent_property(results: list[dict]) -> str:
    blocks = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        query = result.get("query") or {}
        filters = query.get("filters") or {}
        for listing in (result.get("listings") or []):
            name = listing.get("name") or "(이름 없음)"
            code = listing.get("code") or "(코드 없음)"
            parts = [f"이름: {name} | 코드: {code}"]
            addr = listing.get("address") or {}
            if addr.get("road"):
                parts.append(f"주소: {addr['road']}")
            elif addr.get("jibun"):
                parts.append(f"주소: {addr['jibun']}")

            rent_unit = listing.get("rent_unit") or {}
            if rent_unit.get("floor_label"):
                parts.append(f"호실/층: {rent_unit['floor_label']}")
            if rent_unit.get("rental_area_sqm") is not None:
                parts.append(f"임대면적: {rent_unit['rental_area_sqm']}㎡")
            if rent_unit.get("exclusive_area_sqm") is not None:
                parts.append(f"전용면적: {rent_unit['exclusive_area_sqm']}㎡")
            if rent_unit.get("move_in_date_text"):
                parts.append(f"입주시기: {rent_unit['move_in_date_text']}")

            deposit = rent_unit.get("deposit") or {}
            if deposit.get("human"):
                parts.append(f"보증금: {deposit['human']}")
            monthly_rent = rent_unit.get("monthly_rent") or {}
            if monthly_rent.get("human"):
                parts.append(f"월임대료: {monthly_rent['human']}")
            maintenance_fee = rent_unit.get("maintenance_fee") or {}
            if maintenance_fee.get("human"):
                parts.append(f"관리비: {maintenance_fee['human']}")

            station = listing.get("nearest_station") or {}
            if station.get("name"):
                parts.append(f"인접역: {station['name']} ({station.get('distance_m')}m)")

            matched_filters = []
            if filters.get("exclusive_area_max") is not None:
                matched_filters.append(f"전용면적 최대 {filters['exclusive_area_max']}㎡")
            if filters.get("exclusive_area_min") is not None:
                matched_filters.append(f"전용면적 최소 {filters['exclusive_area_min']}㎡")
            if filters.get("rental_area_max") is not None:
                matched_filters.append(f"임대면적 최대 {filters['rental_area_max']}㎡")
            if filters.get("rental_area_min") is not None:
                matched_filters.append(f"임대면적 최소 {filters['rental_area_min']}㎡")
            if matched_filters:
                parts.append(f"적용필터: {', '.join(matched_filters)}")

            blocks.append("\n".join(parts))
    return "\n\n".join(blocks) if blocks else "조회 결과 없음"


def _summarize_land_price_trend(results: list[dict]) -> str:
    lines = []
    for result in results[:_MAX_ITEMS_PER_SECTION]:
        lines.append(_short_json({
            "summary": result.get("summary"),
            "trend": result.get("trend"),
        }))
    return "\n".join(lines) if lines else "조회 결과 없음"


def summarize_tool_results(tool_name: str, results: list[dict]) -> str:
    if tool_name == "get_building_registry":
        return _summarize_building_registry(results)
    if tool_name == "get_land_price":
        return _summarize_land_price(results)
    if tool_name == "get_transaction_history":
        return _summarize_transaction_history(results)
    if tool_name == "get_building_price":
        return _summarize_building_price(results)
    if tool_name == "search_commercial_area":
        return _summarize_commercial_area(results)
    if tool_name == "get_land_price_trend":
        return _summarize_land_price_trend(results)
    if tool_name == "get_area_transaction_stats":
        return _summarize_area_transaction_stats(results)
    if tool_name == "generic_real_estate_qa":
        return _summarize_generic_real_estate_qa(results)
    if tool_name == "get_suhan_property":
        return _summarize_suhan_property(results)
    if tool_name == "get_suhan_rent_property":
        return _summarize_suhan_rent_property(results)
    return _short_json(results[:_MAX_ITEMS_PER_SECTION])


def build_answer_context(retrieval: dict) -> str:
    sections = []
    for tool_name, results in retrieval.items():
        if tool_name in _ANSWER_EXCLUDED_TOOLS:
            continue
        label = _TOOL_LABELS.get(tool_name, tool_name)
        valid = [r for r in results if isinstance(r, dict) and "error" not in r]
        errors = [r for r in results if isinstance(r, dict) and "error" in r]
        if valid:
            summary = summarize_tool_results(tool_name, valid)
            sections.append(f"### {label}\n{summary}")
        elif errors:
            msg = errors[0].get("error", "조회 결과 없음")
            sections.append(f"### {label}\n{msg}")

    context = "\n\n".join(sections) if sections else "조회된 데이터 없음"
    if len(context) > _MAX_CONTEXT_CHARS:
        context = context[:_MAX_CONTEXT_CHARS] + "\n\n[중략] 답변용 컨텍스트 길이 제한으로 일부 데이터 생략"
    return context
