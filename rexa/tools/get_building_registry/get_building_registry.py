from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import (
    normalize_bjdong_code,
    normalize_sigungu_code,
    normalize_lot,
    parse_int,
    run_sql,
    sql_quote,
)
from rexa.tools.get_building_registry.get_building_registry_building_dto import GetBuildingRegistryBuildingDto
from rexa.tools.get_building_registry.get_building_registry_input_dto import GetBuildingRegistryInputDto
from rexa.tools.get_building_registry.get_building_registry_query_dto import GetBuildingRegistryQueryDto
from rexa.tools.get_building_registry.get_building_registry_result_dto import GetBuildingRegistryResultDto

log = setup_logger()


@tool(args_schema=GetBuildingRegistryInputDto)
def get_building_registry(
    sigungu_code: str,
    bjdong_code: str,
    bun: str,
    ji: str = "",
    mgm_bldrgst_pk: str | None = None,
) -> GetBuildingRegistryResultDto:
    """
    특정 건물의 건축물대장 정보를 조회합니다.

    사용 시점:
    - 특정 건물의 용도, 연면적, 대지면적, 층수, 구조, 준공연도 등을 묻는 질문
    - 건물 매입 검토 전 기초 건물 정보를 확인할 때

    조회 방식:
    - 주소 기반: `sigungu_code + bjdong_code + bun + ji`
    - 관리 PK 보조 조건: `mgm_bldrgst_pk`

    반환:
    - `building`: 조회된 단일 건물. 건물명, 주소, 용도, 구조, 면적, 층수, 준공연도 등이 포함됩니다.
    """
    mgm_bldrgst_pk_value = (mgm_bldrgst_pk or "").strip()
    bun_value = bun
    normalized_gu = normalize_sigungu_code(sigungu_code)
    normalized_dong = normalize_bjdong_code(bjdong_code)
    normalized_bun = normalize_lot(bun_value) if bun_value else ""
    normalized_ji = normalize_lot(ji, default="0000") if ji else "0000"

    log.info(
        f"[툴][get_building_registry] 시작 ▶ 단건조회 | "
        f"sigungu_code={sigungu_code!r}→{normalized_gu!r} "
        f"bjdong_code={bjdong_code!r}→{normalized_dong!r} "
        f"bun={bun_value!r}→{normalized_bun!r} ji={ji!r}→{normalized_ji!r} "
        f"mgm_bldrgst_pk={mgm_bldrgst_pk_value!r}"
    )
    if not (normalized_gu and normalized_dong and bun_value):
        log.error(
            f"[툴][get_building_registry] 필수 파라미터 부족 | "
            f"normalized_gu={normalized_gu!r} normalized_dong={normalized_dong!r} bun={bun_value!r}"
        )
        return GetBuildingRegistryResultDto(error="건축물대장 조회에는 sigungu_code, bjdong_code, bun 이 필요합니다. ji는 빈 값으로 전달할 수 있습니다.")

    where_parts = [
        f"b.sigungu_code = {parse_int(normalized_gu)}",
        f"b.bjdong_code = {sql_quote(normalized_dong)}",
        f"b.bun = {sql_quote(normalized_bun)}",
        f"b.ji = {sql_quote(normalized_ji)}",
    ]
    if mgm_bldrgst_pk_value:
        where_parts.append(f"b.mgm_bldrgst_pk = {sql_quote(mgm_bldrgst_pk_value)}")
    where_clause = " AND ".join(where_parts)

    sql_query = f"""
    SELECT
        b.mgm_bldrgst_pk,
        b.plat_plc,
        b.new_plat_plc,
        b.bld_nm,
        b.dong_nm,
        b.main_purps_cd_nm,
        b.strct_cd_nm,
        b.plat_area,
        b.arch_area,
        b.tot_area,
        b.bc_rat,
        b.vl_rat,
        b.grnd_flr_cnt,
        b.ugrnd_flr_cnt,
        b.hhld_cnt,
        b.fmly_cnt,
        b.ho_cnt,
        b.use_apr_day,
        b.use_apr_year,
        b.lat,
        b.lng
    FROM br_title b
    WHERE {where_clause}
    LIMIT 1
    """

    log.info(f"[툴][get_building_registry] query : ${sql_query}")

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_building_registry] DB 조회 실패 | {exc}")
        return GetBuildingRegistryResultDto(error="건축물대장 조회 실패", detail=str(exc))

    if not rows:
        log.warning("[툴][get_building_registry] 결과 없음 — 해당 주소 조건에 건물 데이터 없음")
        return GetBuildingRegistryResultDto(
            error="해당 조건의 건축물대장 정보를 찾지 못했습니다.",
            # query=GetBuildingRegistryQueryDto(
            #     sigungu_code=sigungu_code,
            #     bjdong_code=bjdong_code,
            #     bun=bun_value,
            #     ji=ji or None,
            #     mgm_bldrgst_pk=mgm_bldrgst_pk_value or None,
            # ),
        )

    log.info("[툴][get_building_registry] 완료 ▶ 1개 건물 조회")
    building = GetBuildingRegistryBuildingDto.model_validate(rows[0])
    log.info("")
    query_dto = GetBuildingRegistryQueryDto(
        sigungu_code=sigungu_code,
        bjdong_code=bjdong_code,
        bun=bun_value,
        ji=ji or None,
        mgm_bldrgst_pk=mgm_bldrgst_pk_value or None,
    )
    return GetBuildingRegistryResultDto(
        # query=query_dto,
        building=building,
    )
