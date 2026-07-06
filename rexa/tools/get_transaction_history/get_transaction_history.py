from datetime import date

from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import (
    normalize_bjdong_code,
    normalize_sigungu_code,
    normalize_lot,
    parse_float,
    parse_int,
    run_sql,
    sql_quote,
)
from rexa.tools.get_transaction_history.get_transaction_history_input_dto import GetTransactionHistoryInputDto
from rexa.tools.get_transaction_history.get_transaction_history_query_dto import GetTransactionHistoryQueryDto
from rexa.tools.get_transaction_history.get_transaction_history_result_dto import GetTransactionHistoryResultDto
from rexa.tools.get_transaction_history.get_transaction_history_transaction_dto import GetTransactionHistoryTransactionDto

log = setup_logger()


@tool(args_schema=GetTransactionHistoryInputDto)
def get_transaction_history(
    sigungu_code: str = "",
    bjdong_code: str = "",
    bun: str = "",
    ji: str = "",
    lat: float | None = None,
    lng: float | None = None,
    radius_meters: int = 1000,
    recent_years: int = 3,
    limit: int = 10,
) -> GetTransactionHistoryResultDto:
    """건물 실거래가와 매매 이력을 조회합니다.

    사용 시점:
    - 실거래가, 매매 이력, 최근 거래 사례
    - 마지막 거래 시점·가격, 주변 최근 거래 사례처럼 거래 자체가 핵심인 질문

    지양:
    - 단순 예상 가격
    - 건물 소개, 입지 평가, 상권 분석
    - 거래/실거래가를 직접 묻지 않은 투자 판단
    - `get_building_price`만으로 답할 수 있는 가격 추정

    조회 방식:
    - 주소: `sigungu_code + bjdong_code + bun (+ ji)`
    - 좌표: `lat + lng + radius_meters`

    반환:
    - `query`: 조회 조건
    - `count`: 거래 수
    - `transactions`: 거래 목록
    """
    limit = max(1, min(limit, 100))
    radius_meters = max(1, min(radius_meters, 5000))
    recent_years = max(1, min(recent_years, 30))
    min_deal_year = date.today().year - recent_years + 1

    if lat is not None and lng is not None:
        lat_value = parse_float(lat)
        lng_value = parse_float(lng)
        log.info(f"[툴][get_transaction_history] 시작 ▶ 모드=좌표 | lat={lat_value} lng={lng_value} radius={radius_meters}m recent={recent_years}년")
        if lat_value is None or lng_value is None:
            log.error(f"[툴][get_transaction_history] lat/lng 파싱 실패 | lat={lat!r} lng={lng!r}")
            return GetTransactionHistoryResultDto(error="lat/lng 값이 올바르지 않습니다.")
        where_clause = (
            "b.geog IS NOT NULL AND "
            f"ST_DWithin(b.geog, ST_SetSRID(ST_MakePoint({lng_value}, {lat_value}), 4326)::geography, {radius_meters})"
        )
        distance_select = (
            ", round(ST_Distance("
            f"b.geog, ST_SetSRID(ST_MakePoint({lng_value}, {lat_value}), 4326)::geography"
            "))::integer AS distance_m"
        )
    else:
        normalized_gu = normalize_sigungu_code(sigungu_code)
        normalized_dong = normalize_bjdong_code(bjdong_code)
        normalized_bun = normalize_lot(bun) if bun else ""
        normalized_ji = normalize_lot(ji, default="0000")
        log.info(
            f"[툴][get_transaction_history] 시작 ▶ 모드=주소 | "
            f"sigungu_code={sigungu_code!r}→{normalized_gu!r} bjdong_code={bjdong_code!r}→{normalized_dong!r} "
            f"bun={bun!r}→{normalized_bun!r} ji={ji!r}→{normalized_ji!r} recent={recent_years}년"
        )
        if not (normalized_gu and normalized_dong and bun):
            log.error(
                f"[툴][get_transaction_history] 필수 파라미터 부족 | "
                f"normalized_gu={normalized_gu!r} normalized_dong={normalized_dong!r} bun={bun!r}"
            )
            return GetTransactionHistoryResultDto(error="실거래가 조회에는 주소 또는 좌표 조건이 필요합니다.")
        where_clause = (
            f"b.sigungu_code = {parse_int(normalized_gu)} AND "
            f"b.bjdong_code = {sql_quote(normalized_dong)} AND "
            f"b.bun = {sql_quote(normalized_bun)} AND "
            f"b.ji = {sql_quote(normalized_ji)}"
        )
        distance_select = ""

    sql_query = f"""
    SELECT
        t.id AS rtm_id,
        t.deal_year,
        t.deal_month,
        t.deal_day,
        t.deal_amount,
        t.building_use,
        t.building_type,
        t.land_use,
        t.plottage_ar,
        t.building_ar,
        t.floor,
        t.sigungu_code,
        t.sigungu_name,
        t.bjdong_code,
        t.bjdong_name,
        t.jibun,
        b.mgm_bldrgst_pk,
        b.plat_plc,
        b.new_plat_plc,
        b.bld_nm,
        b.lat,
        b.lng,
        m.match_method,
        m.confidence,
        m.area_diff_pct,
        m.year_diff
        {distance_select}
    FROM rtm_nrg_trade t
    JOIN rtm_br_match m
      ON m.rtm_id = t.id
     AND m.is_primary = true
    JOIN br_title b
      ON b.mgm_bldrgst_pk = m.mgm_bldrgst_pk
    WHERE {where_clause}
      AND t.deal_year >= {min_deal_year}
    ORDER BY
        {"distance_m ASC," if distance_select else ""}
        t.deal_year DESC,
        t.deal_month DESC,
        t.deal_day DESC,
        t.id DESC
    LIMIT {limit}
    """

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_transaction_history] DB 조회 실패 | {exc}")
        return GetTransactionHistoryResultDto(error="실거래가 조회 실패", detail=str(exc))

    if not rows:
        log.warning(f"[툴][get_transaction_history] 결과 없음 | {min_deal_year}년 이후 거래 데이터 없음")
    else:
        log.info(f"[툴][get_transaction_history] 완료 ▶ {len(rows)}건 거래 조회")

    transactions = [GetTransactionHistoryTransactionDto.from_row(row) for row in rows]

    return GetTransactionHistoryResultDto(
        query=GetTransactionHistoryQueryDto(
            sigungu_code=sigungu_code or None,
            bjdong_code=bjdong_code or None,
            bun=bun or None,
            ji=ji or None,
            lat=lat,
            lng=lng,
            radius_meters=radius_meters if lat is not None and lng is not None else None,
            recent_years=recent_years,
            limit=limit,
        ),
        count=len(transactions),
        transactions=transactions,
    )
