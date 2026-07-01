from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import (
    normalize_bjdong_code,
    normalize_sigungu_code,
    normalize_lot,
    run_sql,
    sql_quote,
)
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_filters_dto import GetSuhanRentPropertyFiltersDto
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_input_dto import GetSuhanRentPropertyInputDto
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_listing_dto import GetSuhanRentPropertyListingDto
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_query_dto import GetSuhanRentPropertyQueryDto
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_result_dto import GetSuhanRentPropertyResultDto

log = setup_logger()

_LISTING_SELECT = """
    p.id AS property_id,
    p.name,
    p.code,
    p.base_url,
    p.jibun_addr,
    p.road_addr,
    p.sigungu_code,
    p.bjdong_code,
    p.bun,
    p.ji,
    p.floors,
    p.lat,
    p.lng,
    p.min_stn_dist,
    p.min_stn_name,
    u.id AS unit_id,
    u.floor_label,
    u.rental_area,
    u.exclusive_area,
    u.deposit,
    u.monthly_rent,
    u.maintenance_fee,
    u.move_in_date_text
"""


def _format_area(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}".rstrip("0").rstrip(".") + "㎡"


@tool(args_schema=GetSuhanRentPropertyInputDto)
def get_suhan_rent_property(
    lat: float | None = None,
    lng: float | None = None,
    radius_m: float = 3000,
    sigungu_code: str = "",
    bjdong_code: str = "",
    bun: str = "",
    ji: str = "",
    code: str = "",
    rental_area_min: float | None = None,
    rental_area_max: float | None = None,
    exclusive_area_min: float | None = None,
    exclusive_area_max: float | None = None,
    deposit_min: float | None = None,
    deposit_max: float | None = None,
    monthly_rent_min: float | None = None,
    monthly_rent_max: float | None = None,
    maintenance_fee_min: float | None = None,
    maintenance_fee_max: float | None = None,
    min_stn_dist_min: float | None = None,
    min_stn_dist_max: float | None = None,
) -> GetSuhanRentPropertyResultDto:
    """서안개발 임대 매물 데이터를 검색합니다.

    사용 시점:
    - "임대 매물 있어?", "임대 가능한 공간 알려줘", "월세 얼마야?" 같은 임대 관련 질문

    조회 방식:
    - 좌표 반경 검색: `lat + lng (+ radius_m)`
    - 지번 주소 검색: `sigungu_code + bjdong_code (+ bun + ji)`
    - 코드 검색: `code`

    추가 필터:
    - 임대면적, 전용면적, 보증금, 월 임대료, 관리비, 역거리 조건을 함께 줄 수 있습니다.

    반환:
    - `query`: 실제 검색 모드와 사용된 조건
    - `count`: 반환 임대 유닛 수
    - `listings`: 임대 유닛 목록. 매물 정보, 층, 면적, 보증금, 월 임대료, 관리비가 포함됩니다.
    """
    log.info(
        f"[툴][get_suhan_rent_property] 시작 ▶ "
        f"lat={lat} lng={lng} radius={radius_m}m "
        f"sigungu_code={sigungu_code!r} bjdong_code={bjdong_code!r} bun={bun!r} ji={ji!r} code={code!r} "
        f"rental_area=[{rental_area_min},{rental_area_max}] exclusive_area=[{exclusive_area_min},{exclusive_area_max}] "
        f"deposit=[{deposit_min},{deposit_max}] monthly_rent=[{monthly_rent_min},{monthly_rent_max}] "
        f"maintenance_fee=[{maintenance_fee_min},{maintenance_fee_max}] stn=[{min_stn_dist_min},{min_stn_dist_max}]"
    )

    base_filters: list[str] = [
        "p.is_active = true",
        "u.is_active = true",
        "p.property_type = '임대'",
        "p.code = 'P1761726365421'",
    ]

    if rental_area_min is not None:
        base_filters.append(f"u.rental_area >= {rental_area_min}")
    if rental_area_max is not None:
        base_filters.append(f"u.rental_area <= {rental_area_max}")
    if exclusive_area_min is not None:
        base_filters.append(f"u.exclusive_area >= {exclusive_area_min}")
    if exclusive_area_max is not None:
        base_filters.append(f"u.exclusive_area <= {exclusive_area_max}")
    if deposit_min is not None:
        base_filters.append(f"u.deposit >= {int(deposit_min)}")
    if deposit_max is not None:
        base_filters.append(f"u.deposit <= {int(deposit_max)}")
    if monthly_rent_min is not None:
        base_filters.append(f"u.monthly_rent >= {int(monthly_rent_min)}")
    if monthly_rent_max is not None:
        base_filters.append(f"u.monthly_rent <= {int(monthly_rent_max)}")
    if maintenance_fee_min is not None:
        base_filters.append(f"u.maintenance_fee >= {int(maintenance_fee_min)}")
    if maintenance_fee_max is not None:
        base_filters.append(f"u.maintenance_fee <= {int(maintenance_fee_max)}")
    if min_stn_dist_min is not None:
        base_filters.append(f"p.min_stn_dist >= {min_stn_dist_min}")
    if min_stn_dist_max is not None:
        base_filters.append(f"p.min_stn_dist <= {min_stn_dist_max}")

    where_base = " AND ".join(base_filters)
    join_clause = "JOIN suhan_rent_unit u ON u.code = p.code"

    # 조회방법 1: 위경도 기반 반경 검색
    if lat is not None and lng is not None:
        search_mode = "radius"
        sql_query = f"""
        SELECT
            {_LISTING_SELECT},
            round(
                ST_Distance(
                    p.geog,
                    ST_MakePoint({lng}, {lat})::geography
                )
            )::integer AS distance_m
        FROM suhan_property p
        {join_clause}
        WHERE {where_base}
          AND ST_DWithin(
              p.geog,
              ST_MakePoint({lng}, {lat})::geography,
              {radius_m}
          )
        ORDER BY p.geog <-> ST_MakePoint({lng}, {lat})::geography, u.id
        LIMIT 30
        """

    # 조회방법 2: 지번 주소 기반 검색
    elif sigungu_code or bjdong_code:
        search_mode = "address"
        normalized_gu = normalize_sigungu_code(sigungu_code) if sigungu_code else ""
        normalized_dong = normalize_bjdong_code(bjdong_code) if bjdong_code else ""
        normalized_bun = normalize_lot(bun) if bun else ""
        normalized_ji = normalize_lot(ji, default="") if ji else ""

        addr_filters = list(base_filters)
        if normalized_gu:
            addr_filters.append(f"p.sigungu_code = {sql_quote(normalized_gu)}")
        if normalized_dong:
            addr_filters.append(f"p.bjdong_code = {sql_quote(normalized_dong)}")
        if normalized_bun:
            addr_filters.append(f"p.bun = {sql_quote(normalized_bun)}")
        if normalized_ji:
            addr_filters.append(f"p.ji = {sql_quote(normalized_ji)}")

        sql_query = f"""
        SELECT
            {_LISTING_SELECT}
        FROM suhan_property p
        {join_clause}
        WHERE {" AND ".join(addr_filters)}
        ORDER BY p.id, u.id
        LIMIT 30
        """

    # 조회방법 3: 코드 기반 검색
    elif code:
        search_mode = "code"
        sql_query = f"""
        SELECT
            {_LISTING_SELECT}
        FROM suhan_property p
        {join_clause}
        WHERE {where_base}
          AND p.code = {sql_quote(code)}
        ORDER BY p.id, u.id
        LIMIT 30
        """

    else:
        log.warning("[툴][get_suhan_rent_property] 조회 조건 없음")
        return GetSuhanRentPropertyResultDto(error="위경도, 지번 주소(sigungu_code/bjdong_code), 또는 code 중 하나 이상을 입력해야 합니다.")

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_suhan_rent_property] DB 조회 실패 | {exc}")
        return GetSuhanRentPropertyResultDto(error="임대 매물 조회 실패", detail=str(exc))

    if not rows:
        log.info("[툴][get_suhan_rent_property] 결과 없음")
        return GetSuhanRentPropertyResultDto(error="조건에 맞는 서안개발 임대 매물이 없습니다.")

    listings = [GetSuhanRentPropertyListingDto.from_row(row) for row in rows]
    log.info(f"[툴][get_suhan_rent_property] 완료 ▶ {len(rows)}개 임대 유닛")

    return GetSuhanRentPropertyResultDto(
        query=GetSuhanRentPropertyQueryDto(
            search_mode=search_mode,
            lat=lat,
            lng=lng,
            radius_m=radius_m if lat is not None and lng is not None else None,
            sigungu_code=sigungu_code or None,
            bjdong_code=bjdong_code or None,
            bun=bun or None,
            ji=ji or None,
            code=code or None,
            filters=GetSuhanRentPropertyFiltersDto(
                rental_area_min=rental_area_min,
                rental_area_max=rental_area_max,
                exclusive_area_min=exclusive_area_min,
                exclusive_area_max=exclusive_area_max,
                deposit_min=deposit_min,
                deposit_max=deposit_max,
                monthly_rent_min=monthly_rent_min,
                monthly_rent_max=monthly_rent_max,
                maintenance_fee_min=maintenance_fee_min,
                maintenance_fee_max=maintenance_fee_max,
                min_stn_dist_min=min_stn_dist_min,
                min_stn_dist_max=min_stn_dist_max,
            ),
        ),
        count=len(listings),
        listings=listings,
    )
