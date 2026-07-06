from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._utils import (
    normalize_bjdong_code,
    normalize_lot,
    normalize_sigungu_code,
    parse_int,
    run_sql,
    sql_quote,
)
from rexa.tools.get_land_price.get_land_price_input_dto import GetLandPriceInputDto
from rexa.tools.get_land_price.get_land_price_latest_dto import GetLandPriceLatestDto
from rexa.tools.get_land_price.get_land_price_query_dto import GetLandPriceQueryDto
from rexa.tools.get_land_price.get_land_price_result_dto import GetLandPriceResultDto

log = setup_logger()


@tool(args_schema=GetLandPriceInputDto)
def get_land_price(
    sigungu_code: str,
    bjdong_code: str,
    bun: str,
    ji: str = "",
    base_year: int | None = None,
) -> GetLandPriceResultDto:
    """특정 필지의 최신 공시지가를 단건 조회합니다.

    사용 시점:
    - 공시지가, 토지 가격, 지가를 직접 묻는 질문

    파라미터:
    - `sigungu_code`, `bjdong_code`, `bun`, `ji`: 대상 필지 식별자
    - `base_year`: 특정 시점 기준 조회 시만 사용

    반환:
    - `query`: 조회 조건
    - `latest`: 최신 1건
    """
    normalized_gu = normalize_sigungu_code(sigungu_code)
    normalized_dong = normalize_bjdong_code(bjdong_code)
    normalized_bun = normalize_lot(bun) if bun else ""
    normalized_ji = normalize_lot(ji, default="0000")

    log.info(
        f"[툴][get_land_price] 시작 ▶ "
        f"sigungu_code={sigungu_code!r}→{normalized_gu!r} bjdong_code={bjdong_code!r}→{normalized_dong!r} "
        f"bun={bun!r}→{normalized_bun!r} ji={ji!r}→{normalized_ji!r} base_year={base_year}"
    )

    if not (normalized_gu and normalized_dong and bun):
        log.error(
            f"[툴][get_land_price] 필수 파라미터 부족 | "
            f"normalized_gu={normalized_gu!r} normalized_dong={normalized_dong!r} bun={bun!r}"
        )
        return GetLandPriceResultDto(error="공시지가 조회에는 sigungu_code, bjdong_code, bun 이 필요합니다.")

    base_year_filter = f"AND base_year <= {base_year}" if base_year is not None else ""
    sql_query = f"""
    SELECT
        sigungu_code,
        bjdong_code,
        main_lot_number,
        sub_lot_number,
        base_year,
        base_year_month,
        price_per_sqm,
        parcel_type_name
    FROM official_land_price
    WHERE sigungu_code = {sql_quote(normalized_gu)}
      AND bjdong_code = {sql_quote(normalized_dong)}
      AND main_lot_number = {sql_quote(normalized_bun)}
      AND sub_lot_number = {sql_quote(normalized_ji)}
      {base_year_filter}
    ORDER BY base_year DESC, base_year_month DESC
    LIMIT 1
    """

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_land_price] DB 조회 실패 | {exc}")
        return GetLandPriceResultDto(error="공시지가 조회 실패", detail=str(exc))

    if not rows:
        log.warning(
            f"[툴][get_land_price] 결과 없음 | "
            f"sigungu_code={normalized_gu} bjdong_code={normalized_dong} bun={normalized_bun} ji={normalized_ji} base_year={base_year}"
        )
        return GetLandPriceResultDto(
            error="공시지가를 찾을 수 없습니다.",
            sigungu_code=normalized_gu,
            bjdong_code=normalized_dong,
            bun=normalized_bun,
            ji=normalized_ji,
        )

    row = rows[0]
    latest = GetLandPriceLatestDto.model_construct(
        sigungu_code=(row.get("sigungu_code") or None),
        bjdong_code=(row.get("bjdong_code") or None),
        main_lot_number=(row.get("main_lot_number") or None),
        sub_lot_number=(row.get("sub_lot_number") or None),
        base_year=parse_int(row.get("base_year")),
        base_year_month=(str(row.get("base_year_month")).strip() if row.get("base_year_month") not in (None, "") else None),
        price_per_sqm=(
            None
            if row.get("price_per_sqm") in (None, "")
            else KrwAmountDto.from_amount(row.get("price_per_sqm"))
        ),
        parcel_type_name=(row.get("parcel_type_name") or None),
    )
    log.info(
        f"[툴][get_land_price] 완료 ▶ "
        f"{latest.base_year}년 {latest.price_per_sqm.human if latest.price_per_sqm else '-'}원/㎡"
    )

    return GetLandPriceResultDto(
        query=GetLandPriceQueryDto(
            sigungu_code=normalized_gu,
            bjdong_code=normalized_dong,
            bun=normalized_bun,
            ji=normalized_ji,
            base_year=base_year,
        ),
        latest=latest,
    )
