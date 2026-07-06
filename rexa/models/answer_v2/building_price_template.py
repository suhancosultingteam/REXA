import re

from rexa.tools._utils import parse_float, parse_int

_PYEONG_SQM = 3.305785
_NO_DATA = "정보 없음"

BUILDING_PRICE_TEMPLATE = """입력하신 주소 기준으로 확인 가능한 정보를 간단히 정리해드릴게요.
※ 본 내용은 건축물대장, 공시지가, 실거래 및 주변 시세 데이터를 바탕으로 한 참고용 1차 검토입니다.
실제 매수·매각·대출·세무 판단은 별도 확인이 필요합니다.
건물 개요
주소: {address}
용도: {main_usage}
규모: 지하 {basement_floors}층 / 지상 {ground_floors}층
대지면적: {land_area_sqm}㎡ (약 {land_area_pyeong}평)
연면적: {gross_floor_area_sqm}㎡ (약 {gross_floor_area_pyeong}평)
사용승인일: {approval_date}

가격 참고
렉사 추정가: 약 {estimated_price}억 원 (대지 평당 약 {estimated_land_price_per_pyeong}억 원)
※ 렉사 추정가는 공시지가, 주변 실거래, 면적, 입지 조건 등을 바탕으로 한 내부 산정값이며, 감정평가액이나 실제 거래 가능가와 다를 수 있습니다.

종합 의견
{summary_comment}"""


def _first_valid_result(results: list[dict] | None) -> dict | None:
    for result in results or []:
        if isinstance(result, dict) and "error" not in result:
            return result
    return None


def _to_sqm_str(value: float | None) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".") if value is not None else _NO_DATA


def _to_pyeong_str(sqm: float | None) -> str:
    if sqm is None:
        return _NO_DATA
    pyeong = sqm / _PYEONG_SQM
    return f"{pyeong:.1f}".rstrip("0").rstrip(".")


def _format_approval_date(use_apr_day: str | None, use_apr_year: int | str | None) -> str:
    if use_apr_day:
        digits = re.sub(r"\D", "", str(use_apr_day))
        if len(digits) == 8:
            return f"{digits[:4]}.{digits[4:6]}.{digits[6:8]}"
        return str(use_apr_day)
    if use_apr_year:
        return f"{use_apr_year}년"
    return _NO_DATA


def _build_commercial_area_summary(retrieval: dict) -> str:
    commercial_result = _first_valid_result(retrieval.get("search_commercial_area"))
    if not commercial_result:
        return "조회된 상권 데이터가 없습니다."

    chunks = [c for c in (commercial_result.get("chunks") or []) if isinstance(c, dict) and c.get("text")]
    if not chunks:
        return "조회된 상권 데이터가 없습니다."

    texts = [str(c["text"]).strip() for c in chunks[:2]]
    return " ".join(texts)


def _build_summary_comment(price_result: dict, retrieval: dict) -> str:
    parts: list[str] = []

    comparable_count = parse_int(price_result.get("comparable_count"))
    if comparable_count:
        parts.append(f"주변 비교 거래사례 {comparable_count}건을 기준으로 산정한 참고용 추정가입니다.")
    else:
        parts.append("현재 조회된 데이터를 기준으로 산정한 참고용 추정가입니다.")

    adjustments = price_result.get("adjustments") or []
    reasons = [
        a.get("reason") for a in adjustments
        if isinstance(a, dict) and a.get("reason")
    ]
    if reasons:
        parts.append(" ".join(str(r).strip() for r in reasons[:3]))

    has_transactions = bool(
        [r for r in retrieval.get("get_transaction_history") or [] if isinstance(r, dict) and "error" not in r]
    )
    if has_transactions:
        parts.append("인근 실거래 이력도 함께 참고하시기 바랍니다.")

    parts.append("정확한 매수·매각·대출·세무 판단은 별도 검토가 필요합니다.")
    return " ".join(parts)


def try_build_building_price_answer(origin: str, retrieval: dict) -> str | None:
    price_result = _first_valid_result(retrieval.get("get_building_price"))
    if price_result is None:
        return None

    target_building = price_result.get("target_building") or {}
    registry_result = _first_valid_result(retrieval.get("get_building_registry")) or {}
    registry_building = registry_result.get("building") or {}

    address = (
        registry_building.get("new_plat_plc")
        or registry_building.get("plat_plc")
        or target_building.get("new_plat_plc")
        or target_building.get("plat_plc")
        or _NO_DATA
    )
    main_usage = registry_building.get("main_purps_cd_nm") or target_building.get("main_purps_cd_nm") or _NO_DATA
    ground_floors = parse_int(registry_building.get("grnd_flr_cnt"))
    basement_floors = parse_int(registry_building.get("ugrnd_flr_cnt"))

    land_area_sqm = parse_float(registry_building.get("plat_area")) or parse_float(target_building.get("plat_area"))
    gross_floor_area_sqm = parse_float(registry_building.get("tot_area")) or parse_float(target_building.get("tot_area"))

    approval_date = _format_approval_date(
        registry_building.get("use_apr_day"),
        registry_building.get("use_apr_year") or target_building.get("use_apr_year"),
    )

    final_estimated_price = price_result.get("final_estimated_price") or {}
    estimated_price_krw = parse_float(final_estimated_price.get("krw"))
    estimated_price = f"{estimated_price_krw / 1e8:.1f}".rstrip("0").rstrip(".") if estimated_price_krw is not None else _NO_DATA

    land_area_pyeong = land_area_sqm / _PYEONG_SQM if land_area_sqm else None
    if estimated_price_krw is not None and land_area_pyeong:
        estimated_land_price_per_pyeong = f"{estimated_price_krw / 1e8 / land_area_pyeong:.2f}".rstrip("0").rstrip(".")
    else:
        estimated_land_price_per_pyeong = _NO_DATA

    return BUILDING_PRICE_TEMPLATE.format(
        address=address,
        main_usage=main_usage,
        basement_floors=basement_floors if basement_floors is not None else _NO_DATA,
        ground_floors=ground_floors if ground_floors is not None else _NO_DATA,
        land_area_sqm=_to_sqm_str(land_area_sqm),
        land_area_pyeong=_to_pyeong_str(land_area_sqm),
        gross_floor_area_sqm=_to_sqm_str(gross_floor_area_sqm),
        gross_floor_area_pyeong=_to_pyeong_str(gross_floor_area_sqm),
        approval_date=approval_date,
        estimated_price=estimated_price,
        estimated_land_price_per_pyeong=estimated_land_price_per_pyeong,
        commercial_area_summary=_build_commercial_area_summary(retrieval),
        summary_comment=_build_summary_comment(price_result, retrieval),
    )
