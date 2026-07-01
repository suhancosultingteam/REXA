from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import (
    normalize_bjdong_code,
    normalize_sigungu_code,
    normalize_lot,
    run_sql,
    sql_quote,
)
from rexa.tools.get_suhan_property.get_suhan_property_filters_dto import GetSuhanPropertyFiltersDto
from rexa.tools.get_suhan_property.get_suhan_property_input_dto import GetSuhanPropertyInputDto
from rexa.tools.get_suhan_property.get_suhan_property_listing_dto import GetSuhanPropertyListingDto
from rexa.tools.get_suhan_property.get_suhan_property_query_dto import GetSuhanPropertyQueryDto
from rexa.tools.get_suhan_property.get_suhan_property_result_dto import GetSuhanPropertyResultDto

log = setup_logger()

_LISTING_SELECT = """
    id,
    name,
    code,
    base_url,
    jibun_addr,
    road_addr,
    sigungu_code,
    bjdong_code,
    bun,
    ji,
    price,
    land_area,
    total_area,
    floors,
    lat,
    lng,
    min_stn_dist,
    min_stn_name
"""


@tool(args_schema=GetSuhanPropertyInputDto)
def get_suhan_property(
    lat: float | None = None,
    lng: float | None = None,
    radius_m: float = 3000,
    sigungu_code: str = "",
    bjdong_code: str = "",
    bun: str = "",
    ji: str = "",
    code: str = "",
    land_area_min: float | None = None,
    land_area_max: float | None = None,
    total_area_min: float | None = None,
    total_area_max: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    min_stn_dist_min: float | None = None,
    min_stn_dist_max: float | None = None,
) -> GetSuhanPropertyResultDto:
    """서안개발 자체 매물 데이터를 검색합니다.

    사용 시점:
    - "매물 보여줘", "근처 매물 있어?", "이 주소 매물 알려줘" 같은 매물 조회 질문

    조회 방식:
    - 좌표 반경 검색: `lat + lng (+ radius_m)`
    - 지번 주소 검색: `sigungu_code + bjdong_code (+ bun + ji)`
    - 코드 검색: `code`

    추가 필터:
    - 면적, 가격, 역거리 조건을 함께 줄 수 있습니다.

    반환:
    - `query`: 실제 검색 모드와 사용된 조건
    - `count`: 반환 매물 수
    - `listings`: 매물 목록. 코드, 주소, 가격, 면적, 거리, 역 정보가 포함됩니다.
    """
    log.info(
        f"[툴][get_suhan_property] 시작 ▶ "
        f"lat={lat} lng={lng} radius={radius_m}m "
        f"sigungu_code={sigungu_code!r} bjdong_code={bjdong_code!r} bun={bun!r} ji={ji!r} code={code!r} "
        f"land=[{land_area_min},{land_area_max}] total=[{total_area_min},{total_area_max}] "
        f"price=[{price_min},{price_max}] stn=[{min_stn_dist_min},{min_stn_dist_max}]"
    )

    filters: list[str] = [
        "is_active = true",
        "property_type = '매매'",
    ]

    if land_area_min is not None:
        filters.append(f"land_area >= {land_area_min}")
    if land_area_max is not None:
        filters.append(f"land_area <= {land_area_max}")
    if total_area_min is not None:
        filters.append(f"total_area >= {total_area_min}")
    if total_area_max is not None:
        filters.append(f"total_area <= {total_area_max}")
    if price_min is not None:
        filters.append(f"price >= {int(price_min)}")
    if price_max is not None:
        filters.append(f"price <= {int(price_max)}")
    if min_stn_dist_min is not None:
        filters.append(f"min_stn_dist >= {min_stn_dist_min}")
    if min_stn_dist_max is not None:
        filters.append(f"min_stn_dist <= {min_stn_dist_max}")

    where_base = " AND ".join(filters)

    # 조회방법 1: 위경도 기반 반경 검색
    if lat is not None and lng is not None:
        search_mode = "radius"
        sql_query = f"""
        SELECT
            {_LISTING_SELECT},
            round(
                ST_Distance(
                    geog,
                    ST_MakePoint({lng}, {lat})::geography
                )
            )::integer AS distance_m
        FROM suhan_property
        WHERE {where_base}
          AND ST_DWithin(
              geog,
              ST_MakePoint({lng}, {lat})::geography,
              {radius_m}
          )
        ORDER BY geog <-> ST_MakePoint({lng}, {lat})::geography
        LIMIT 20
        """

    # 조회방법 2: 지번 주소 기반 검색
    elif sigungu_code or bjdong_code:
        search_mode = "address"
        normalized_gu = normalize_sigungu_code(sigungu_code) if sigungu_code else ""
        normalized_dong = normalize_bjdong_code(bjdong_code) if bjdong_code else ""
        normalized_bun = normalize_lot(bun) if bun else ""
        normalized_ji = normalize_lot(ji, default="") if ji else ""

        addr_filters = list(filters)
        if normalized_gu:
            addr_filters.append(f"sigungu_code = {sql_quote(normalized_gu)}")
        if normalized_dong:
            addr_filters.append(f"bjdong_code = {sql_quote(normalized_dong)}")
        if normalized_bun:
            addr_filters.append(f"bun = {sql_quote(normalized_bun)}")
        if normalized_ji:
            addr_filters.append(f"ji = {sql_quote(normalized_ji)}")

        sql_query = f"""
        SELECT
            {_LISTING_SELECT}
        FROM suhan_property
        WHERE {" AND ".join(addr_filters)}
        ORDER BY id
        LIMIT 20
        """

    # 조회방법 3: 코드 기반 검색
    elif code:
        search_mode = "code"
        sql_query = f"""
        SELECT
            {_LISTING_SELECT}
        FROM suhan_property
        WHERE {where_base}
          AND code = {sql_quote(code)}
        ORDER BY id
        LIMIT 20
        """

    else:
        log.warning("[툴][get_suhan_property] 조회 조건 없음")
        return GetSuhanPropertyResultDto(error="위경도, 지번 주소(sigungu_code/bjdong_code), 또는 code 중 하나 이상을 입력해야 합니다.")

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_suhan_property] DB 조회 실패 | {exc}")
        return GetSuhanPropertyResultDto(error="매물 조회 실패", detail=str(exc))

    if not rows:
        log.info("[툴][get_suhan_property] 결과 없음")
        return GetSuhanPropertyResultDto(error="조건에 맞는 서안개발 매물이 없습니다.")

    listings = [GetSuhanPropertyListingDto.from_row(row) for row in rows]
    log.info(f"[툴][get_suhan_property] 완료 ▶ {len(rows)}개 매물")

    return GetSuhanPropertyResultDto(
        query=GetSuhanPropertyQueryDto(
            search_mode=search_mode,
            lat=lat,
            lng=lng,
            radius_m=radius_m if lat is not None and lng is not None else None,
            sigungu_code=sigungu_code or None,
            bjdong_code=bjdong_code or None,
            bun=bun or None,
            ji=ji or None,
            code=code or None,
            filters=GetSuhanPropertyFiltersDto(
                land_area_min=land_area_min,
                land_area_max=land_area_max,
                total_area_min=total_area_min,
                total_area_max=total_area_max,
                price_min=price_min,
                price_max=price_max,
                min_stn_dist_min=min_stn_dist_min,
                min_stn_dist_max=min_stn_dist_max,
            ),
        ),
        count=len(listings),
        listings=listings,
    )
