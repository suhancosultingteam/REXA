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
from rexa.tools.get_land_price_trend.get_land_price_trend_entry_dto import GetLandPriceTrendEntryDto
from rexa.tools.get_land_price_trend.get_land_price_trend_input_dto import GetLandPriceTrendInputDto
from rexa.tools.get_land_price_trend.get_land_price_trend_query_dto import GetLandPriceTrendQueryDto
from rexa.tools.get_land_price_trend.get_land_price_trend_result_dto import GetLandPriceTrendResultDto
from rexa.tools.get_land_price_trend.get_land_price_trend_summary_dto import GetLandPriceTrendSummaryDto

log = setup_logger()


@tool(args_schema=GetLandPriceTrendInputDto)
def get_land_price_trend(
    sigungu_code: str,
    bjdong_code: str,
    bun: str,
    ji: str = "",
) -> GetLandPriceTrendResultDto:
    """특정 필지의 공시지가 추이를 분석합니다.

    사용 시점:
    - "공시지가가 얼마나 올랐어?", "지가 상승률 어때?" 같은 추이 질문

    반환:
    - `query`: 조회한 필지 조건
    - `trend`: 연도별 공시지가와 전년 대비 변화
    - `summary`: 전체 기간 요약. 총 상승률과 CAGR이 포함됩니다.
    """
    normalized_gu = normalize_sigungu_code(sigungu_code)
    normalized_dong = normalize_bjdong_code(bjdong_code)
    normalized_bun = normalize_lot(bun) if bun else ""
    normalized_ji = normalize_lot(ji, default="0000")
    current_year = date.today().year

    log.info(
        f"[툴][get_land_price_trend] 시작 ▶ "
        f"sigungu_code={sigungu_code!r}→{normalized_gu!r} bjdong_code={bjdong_code!r}→{normalized_dong!r} "
        f"bun={bun!r}→{normalized_bun!r} ji={ji!r}→{normalized_ji!r}"
    )

    if not (normalized_gu and normalized_dong and bun):
        return GetLandPriceTrendResultDto(error="공시지가 추이 조회에는 sigungu_code, bjdong_code, bun 이 필요합니다.")

    sql_query = f"""
    WITH target_rows AS (
        SELECT
            base_year,
            price_per_sqm,
            parcel_type_name
        FROM official_land_price
        WHERE sigungu_code = {sql_quote(normalized_gu)}
          AND bjdong_code = {sql_quote(normalized_dong)}
          AND main_lot_number = {sql_quote(normalized_bun)}
          AND sub_lot_number = {sql_quote(normalized_ji)}
          AND base_year <= {current_year}
        ORDER BY base_year DESC
        LIMIT 10
    )
    SELECT *
    FROM target_rows
    ORDER BY base_year ASC
    """

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_land_price_trend] DB 조회 실패 | {exc}")
        return GetLandPriceTrendResultDto(error="공시지가 추이 조회 실패", detail=str(exc))

    if not rows:
        log.warning(f"[툴][get_land_price_trend] 결과 없음 | sigungu_code={normalized_gu} bjdong_code={normalized_dong} bun={normalized_bun}")
        return GetLandPriceTrendResultDto(
            error="공시지가 데이터를 찾을 수 없습니다.",
            sigungu_code=normalized_gu,
            bjdong_code=normalized_dong,
            bun=normalized_bun,
            ji=normalized_ji,
        )

    # 전년 대비 변동액·변동률 계산
    trend: list[GetLandPriceTrendEntryDto] = []
    for i, row in enumerate(rows):
        price = parse_float(row.get("price_per_sqm"))
        yoy_change: int | None = None
        yoy_rate: float | None = None
        if i > 0:
            prev_price = parse_float(rows[i - 1].get("price_per_sqm"))
            if price is not None and prev_price and prev_price > 0:
                yoy_change = round(price - prev_price)
                yoy_rate = round((price - prev_price) / prev_price, 4)
        trend.append(GetLandPriceTrendEntryDto(
            year=parse_int(row.get("base_year")),
            price_per_sqm=price,
            parcel_type_name=row.get("parcel_type_name"),
            yoy_change=yoy_change,
            yoy_rate=yoy_rate,
        ))

    # 전체 기간 요약
    first_price = parse_float(rows[0].get("price_per_sqm"))
    last_price = parse_float(rows[-1].get("price_per_sqm"))
    n = len(rows)

    if first_price and last_price and first_price > 0 and n > 1:
        total_rate = (last_price - first_price) / first_price
        cagr = (last_price / first_price) ** (1 / (n - 1)) - 1
        summary = GetLandPriceTrendSummaryDto(
            years=n,
            start_year=parse_int(rows[0].get("base_year")),
            end_year=parse_int(rows[-1].get("base_year")),
            start_price_per_sqm=round(first_price),
            end_price_per_sqm=round(last_price),
            total_change=round(last_price - first_price),
            total_rate=round(total_rate, 4),
            cagr=round(cagr, 4),
        )
    else:
        summary = GetLandPriceTrendSummaryDto(years=n)

    log.info(
        f"[툴][get_land_price_trend] 완료 ▶ {n}년 데이터 | "
        f"{summary.start_year}→{summary.end_year} | "
        f"총 상승률 {summary.total_rate or 0:.1%} | CAGR {summary.cagr or 0:.1%}"
    )

    return GetLandPriceTrendResultDto(
        query=GetLandPriceTrendQueryDto(
            sigungu_code=normalized_gu,
            bjdong_code=normalized_dong,
            bun=normalized_bun,
            ji=normalized_ji,
        ),
        trend=trend,
        summary=summary,
    )
