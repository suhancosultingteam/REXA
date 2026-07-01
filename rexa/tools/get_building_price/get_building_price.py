from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import median
from typing import Any

from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._utils import (
    format_human_krw,
    normalize_bjdong_code,
    normalize_sigungu_code,
    normalize_lot,
    parse_float,
    parse_int,
    run_sql,
    sql_quote,
)
from rexa.tools.get_building_price.get_building_price_adjustment_dto import GetBuildingPriceAdjustmentDto
from rexa.tools.get_building_price.get_building_price_comparable_dto import GetBuildingPriceComparableDto
from rexa.tools.get_building_price.get_building_price_input_dto import GetBuildingPriceInputDto
from rexa.tools.get_building_price.get_building_price_result_dto import GetBuildingPriceResultDto
from rexa.tools.get_building_price.get_building_price_stage_dto import GetBuildingPriceStageDto
from rexa.tools.get_building_price.get_building_price_target_dto import GetBuildingPriceTargetDto

log = setup_logger()

_ROAD_CONTACT_ADJUSTMENTS = {
    "0": 0.00,
    "1": 0.12,
    "2": 0.15,
    "3": 0.15,
    "4": 0.04,
    "5": 0.07,
    "6": 0.00,
    "7": 0.03,
    "8": -0.05,
    "9": -0.05,
    "10": -0.05,
    "11": -0.05,
}

MIN_REQUIRED_COMPARABLES = 3
MAX_SELECTED_COMPARABLES = 5
LAND_PRICE_BAND_RATIO = 0.30
MAX_CANDIDATE_ROWS = 500

_TERRAIN_SHAPE_ADJUSTMENTS = {
    "00": 0.00,
    "01": 0.03,
    "02": 0.05,
    "03": -0.07,
    "04": -0.03,
    "05": -0.10,
    "06": -0.30,
}


@dataclass(frozen=True)
class Stage:
    name: str
    recent_years: int
    radius_meters: int
    require_same_zoning: bool
    require_land_price_band: bool


def _build_stages() -> list[Stage]:
    stages: list[Stage] = []
    for require_land_price_band in (True, False):
        for radius_meters in (300, 500, 1000):
            for recent_years in (3, 5, 10):
                suffix = "_landprice" if require_land_price_band else ""
                stages.append(
                    Stage(
                        name=f"zoning_{radius_meters}m_{recent_years}y{suffix}",
                        recent_years=recent_years,
                        radius_meters=radius_meters,
                        require_same_zoning=True,
                        require_land_price_band=require_land_price_band,
                    )
                )
    return stages


STAGES: list[Stage] = _build_stages()


def _normalize_code(value: Any) -> str | None:
    if value in (None, ""):
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return None
    return str(int(digits))


def _fetch_target_building(sigungu_code: str, bjdong_code: str, bun: str, ji: str) -> dict[str, str] | None:
    query = f"""
    SELECT
        b.mgm_bldrgst_pk,
        b.plat_plc,
        b.new_plat_plc,
        b.bld_nm,
        b.main_purps_cd_nm,
        b.plat_gb_cd,
        b.plat_area,
        b.tot_area,
        b.use_apr_year,
        b.nearest_station_distance,
        coalesce(b.lat, ST_Y(b.geog::geometry)) AS lat,
        coalesce(b.lng, ST_X(b.geog::geometry)) AS lng
    FROM br_title b
    WHERE b.sigungu_code = {parse_int(sigungu_code)}
      AND b.bjdong_code = {sql_quote(bjdong_code)}
      AND b.bun = {sql_quote(bun)}
      AND b.ji = {sql_quote(ji)}
    ORDER BY
        CASE WHEN b.geog IS NOT NULL THEN 0 ELSE 1 END,
        CASE WHEN coalesce(b.plat_area, 0) > 0 THEN 0 ELSE 1 END,
        b.main_atch_gb_cd ASC NULLS LAST,
        b.plat_area DESC NULLS LAST,
        b.tot_area DESC NULLS LAST
    LIMIT 1
    """
    rows = run_sql(query)
    return rows[0] if rows else None


def _fetch_target_zoning_context(
    sigungu_code: str,
    bjdong_code: str,
    bun: str,
    ji: str,
) -> dict[str, str] | None:
    query = f"""
    SELECT
        zoning_code_1,
        zoning_name_1,
        road_contact_code,
        road_contact_name,
        terrain_shape_code,
        land_area,
        base_year,
        base_month
    FROM individual_land_price
    WHERE sigungu_code = {sql_quote(sigungu_code)}
      AND bjdong_code = {sql_quote(bjdong_code)}
      AND bun = {sql_quote(bun)}
      AND ji = {sql_quote(ji)}
    ORDER BY base_year DESC, base_month DESC
    LIMIT 1
    """
    rows = run_sql(query)
    return rows[0] if rows else None


def _lot_key(sigungu_code: str, bjdong_code: str, main_lot_number: str, sub_lot_number: str) -> tuple[str, str, str, str]:
    return (
        str(sigungu_code),
        str(bjdong_code),
        normalize_lot(main_lot_number),
        normalize_lot(sub_lot_number, default="0000"),
    )


def _lot_key_from_row(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return _lot_key(
        str(row.get("sigungu_code") or ""),
        str(row.get("bjdong_code") or ""),
        str(row.get("bun") or ""),
        str(row.get("ji") or ""),
    )


def _fetch_official_land_price_history(
    lot_keys: list[tuple[str, str, str, str]],
) -> dict[tuple[str, str, str, str], list[dict[str, str]]]:
    unique_keys = list(dict.fromkeys(lot_keys))
    if not unique_keys:
        return {}

    values_sql = ", ".join(
        "("
        f"{sql_quote(sigungu_code)}, "
        f"{sql_quote(bjdong_code)}, "
        f"{sql_quote(main_lot_number)}, "
        f"{sql_quote(sub_lot_number)}"
        ")"
        for sigungu_code, bjdong_code, main_lot_number, sub_lot_number in unique_keys
    )
    query = f"""
    WITH requested_lots (sigungu_code, bjdong_code, main_lot_number, sub_lot_number) AS (
        VALUES {values_sql}
    )
    SELECT
        opl.sigungu_code,
        opl.bjdong_code,
        opl.main_lot_number,
        opl.sub_lot_number,
        opl.base_year,
        opl.base_year_month,
        opl.price_per_sqm
    FROM requested_lots r
    JOIN official_land_price opl
      ON opl.sigungu_code = r.sigungu_code
     AND opl.bjdong_code = r.bjdong_code
     AND opl.main_lot_number = r.main_lot_number
     AND opl.sub_lot_number = r.sub_lot_number
    ORDER BY
        opl.sigungu_code,
        opl.bjdong_code,
        opl.main_lot_number,
        opl.sub_lot_number,
        opl.base_year ASC
    """
    rows = run_sql(query)

    history_map: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = _lot_key(
            row["sigungu_code"],
            row["bjdong_code"],
            row["main_lot_number"],
            row["sub_lot_number"],
        )
        history_map.setdefault(key, []).append(row)
    return history_map


def _pick_current_official_land_price(
    history_rows: list[dict[str, str]],
    reference_land_price_year: int,
) -> dict[str, str] | None:
    if not history_rows:
        return None

    latest_not_after_reference: dict[str, str] | None = None
    latest_any: dict[str, str] | None = None
    for row in history_rows:
        base_year = parse_int(row.get("base_year"))
        if base_year is None:
            continue
        latest_any = row
        if base_year <= reference_land_price_year:
            latest_not_after_reference = row
    return latest_not_after_reference or latest_any


def _pick_historical_official_land_price(
    history_rows: list[dict[str, str]],
    deal_year: int | None,
) -> dict[str, str] | None:
    if not history_rows or deal_year is None:
        return None

    historical: dict[str, str] | None = None
    for row in history_rows:
        base_year = parse_int(row.get("base_year"))
        if base_year is None:
            continue
        if base_year <= deal_year:
            historical = row
    return historical


def _attach_official_land_price_context(
    rows: list[dict[str, str]],
    history_map: dict[tuple[str, str, str, str], list[dict[str, str]]],
    reference_land_price_year: int,
) -> list[dict[str, str]]:
    enriched_rows: list[dict[str, str]] = []
    for row in rows:
        key = _lot_key_from_row(row)
        history_rows = history_map.get(key, [])
        current_row = _pick_current_official_land_price(history_rows, reference_land_price_year)
        historical_row = _pick_historical_official_land_price(
            history_rows,
            parse_int(row.get("deal_year")),
        )

        enriched_row = dict(row)
        enriched_row["current_official_land_price"] = (
            current_row.get("price_per_sqm", "") if current_row else ""
        )
        enriched_row["current_land_price_base_year"] = (
            current_row.get("base_year", "") if current_row else ""
        )
        enriched_row["current_land_price_base_month"] = (
            current_row.get("base_year_month", "") if current_row else ""
        )
        enriched_row["historical_official_land_price"] = (
            historical_row.get("price_per_sqm", "") if historical_row else ""
        )
        enriched_row["historical_land_price_base_year"] = (
            historical_row.get("base_year", "") if historical_row else ""
        )
        enriched_row["historical_land_price_base_month"] = (
            historical_row.get("base_year_month", "") if historical_row else ""
        )
        enriched_rows.append(enriched_row)
    return enriched_rows


def _fetch_candidate_universe(
    lat: float,
    lng: float,
    min_deal_year: int,
    radius_meters: int,
    max_rows: int,
) -> list[dict[str, str]]:
    query = f"""
    SELECT
        t.id AS rtm_id,
        t.deal_year,
        t.deal_month,
        t.deal_day,
        t.deal_amount,
        t.plottage_ar,
        t.building_ar,
        b.mgm_bldrgst_pk,
        b.plat_plc,
        b.new_plat_plc,
        b.bld_nm,
        b.main_purps_cd_nm,
        b.plat_area,
        b.tot_area,
        b.use_apr_year,
        b.sigungu_code,
        b.bjdong_code,
        b.bun,
        b.ji,
        ilp_current.zoning_code_1,
        ilp_current.zoning_name_1,
        ilp_current.road_contact_code,
        ilp_current.road_contact_name,
        ilp_current.land_area AS current_land_area,
        round(
            ST_Distance(
                b.geog,
                ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography
            )
        )::integer AS distance_m
    FROM rtm_nrg_trade t
    JOIN rtm_br_match m
      ON m.rtm_id = t.id
     AND m.is_primary = true
    JOIN br_title b
      ON b.mgm_bldrgst_pk = m.mgm_bldrgst_pk
    LEFT JOIN LATERAL (
        SELECT
            zoning_code_1,
            zoning_name_1,
            road_contact_code,
            road_contact_name,
            land_area
        FROM individual_land_price ilp
        WHERE ilp.sigungu_code = b.sigungu_code::text
          AND ilp.bjdong_code = b.bjdong_code
          AND ilp.bun = b.bun
          AND ilp.ji = b.ji
        ORDER BY ilp.base_year DESC, ilp.base_month DESC
        LIMIT 1
    ) ilp_current ON true
    WHERE b.geog IS NOT NULL
      AND t.deal_amount IS NOT NULL
      AND t.deal_year >= {min_deal_year}
      AND ST_DWithin(
            b.geog,
            ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography,
            {radius_meters}
          )
    ORDER BY distance_m ASC, t.deal_year DESC, t.deal_month DESC, t.deal_day DESC, t.id DESC
    LIMIT {max_rows}
    """
    return run_sql(query)


def _terrain_shape_adjustment(terrain_shape_code: str | None) -> tuple[float, str]:
    if terrain_shape_code in (None, ""):
        return 0.0, "지형 형상 정보 없음"
    code = str(terrain_shape_code).strip()
    if code in _TERRAIN_SHAPE_ADJUSTMENTS:
        return _TERRAIN_SHAPE_ADJUSTMENTS[code], f"지형 형상 코드 {code}"
    return 0.0, f"지형 형상 코드 {code}(기본값)"


def _station_adjustment(distance_m: float | None) -> tuple[float, str]:
    if distance_m is None:
        return 0.0, "역 정보 없음"
    if distance_m <= 150:
        return 0.08, "역접근성 150m 이하"
    if distance_m <= 300:
        return 0.05, "역접근성 150~300m"
    if distance_m <= 500:
        return 0.02, "역접근성 300~500m"
    if distance_m <= 800:
        return 0.0, "역접근성 500~800m"
    if distance_m <= 1200:
        return -0.03, "역접근성 800~1200m"
    return -0.05, "역접근성 1200m 초과"


def _road_adjustment(road_contact_code: str | None) -> tuple[float, str, bool]:
    normalized = _normalize_code(road_contact_code)
    if normalized is None:
        return 0.0, "도로 접면 정보 없음", False
    if normalized == "12":
        return 0.0, "도로 접면 12: 자동 평가 제외", True
    return _ROAD_CONTACT_ADJUSTMENTS.get(normalized, 0.0), f"도로 접면 코드 {normalized}", False


def _age_adjustment(use_apr_year: int | None, current_year: int) -> tuple[float, str]:
    if use_apr_year is None:
        return 0.0, "사용승인연도 없음"
    age = max(0, current_year - use_apr_year)
    if age <= 5:
        return 0.08, f"건축 연식 {age}년"
    if age <= 10:
        return 0.05, f"건축 연식 {age}년"
    if age <= 20:
        return 0.02, f"건축 연식 {age}년"
    if age <= 30:
        return 0.0, f"건축 연식 {age}년"
    if age <= 40:
        return -0.08, f"건축 연식 {age}년"
    return -0.15, f"건축 연식 {age}년"


def _within_band(value: float | None, target: float | None, ratio: float) -> bool:
    if value is None or value <= 0 or target is None or target <= 0:
        return False
    return target * (1 - ratio) <= value <= target * (1 + ratio)


def _stage_matches(stage: Stage, row: dict[str, str], target_ctx: dict[str, Any], min_deal_year: int) -> bool:
    deal_year = parse_int(row.get("deal_year"))
    distance_m = parse_float(row.get("distance_m"))
    if deal_year is None or deal_year < min_deal_year:
        return False
    if distance_m is None or distance_m > stage.radius_meters:
        return False
    if stage.require_same_zoning:
        zoning_code = (row.get("zoning_code_1") or "").strip()
        if not zoning_code or zoning_code != target_ctx["zoning_code_1"]:
            return False
    if stage.require_land_price_band:
        if not _within_band(
            parse_float(row.get("current_official_land_price")),
            target_ctx["official_land_price"],
            LAND_PRICE_BAND_RATIO,
        ):
            return False
    return True


def _stage_to_dto(stage: Stage) -> GetBuildingPriceStageDto:
    return GetBuildingPriceStageDto(
        stage=stage.name,
        recent_years=stage.recent_years,
        radius_meters=stage.radius_meters,
        require_same_zoning=stage.require_same_zoning,
        require_land_price_band=stage.require_land_price_band,
    )


def _stage_summary_dict(stage: Stage) -> dict[str, Any]:
    return _stage_to_dto(stage).model_dump()


def _required_comparables_for_stage(stage: Stage) -> int:
    if stage.radius_meters == 300 and stage.require_land_price_band:
        return 1
    return MIN_REQUIRED_COMPARABLES


def _resolve_comparable_land_area(row: dict[str, str]) -> tuple[float | None, str]:
    land_area = parse_float(row.get("plottage_ar"))
    if land_area and land_area > 0:
        return land_area, "plottage_ar"
    land_area = parse_float(row.get("plat_area"))
    if land_area and land_area > 0:
        return land_area, "br_title.plat_area"
    return None, "unknown"


def _is_usable_comparable(row: dict[str, str]) -> bool:
    deal_amount_krw = parse_float(row.get("deal_amount"))
    land_area, _ = _resolve_comparable_land_area(row)
    return bool(deal_amount_krw and land_area and land_area > 0)


def _pick_stage(
    candidates: list[dict[str, str]],
    target_ctx: dict[str, Any],
    current_year: int,
) -> tuple[Stage | None, list[dict[str, str]], list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for stage in STAGES:
        min_deal_year = current_year - stage.recent_years + 1
        required_count = _required_comparables_for_stage(stage)
        matched_rows = [
            row for row in candidates if _stage_matches(stage, row, target_ctx, min_deal_year)
        ]
        usable_rows = [row for row in matched_rows if _is_usable_comparable(row)]
        attempts.append({
            **_stage_summary_dict(stage),
            "min_deal_year": min_deal_year,
            "matched_count": len(matched_rows),
            "usable_count": len(usable_rows),
            "required_count": required_count,
        })
        log.debug(
            f"[툴][get_building_price] 단계 시도: {stage.name} "
            f"({stage.recent_years}년/{stage.radius_meters}m) → "
            f"매칭 {len(matched_rows)}건 / 유효 {len(usable_rows)}건 "
            f"{'✓ 선택' if len(usable_rows) >= required_count else f'✗ 부족 (최소 {required_count}건)'}"
        )
        if len(usable_rows) >= required_count:
            return stage, usable_rows[:MAX_SELECTED_COMPARABLES], attempts
    return None, [], attempts


def _land_price_adjustment_ratio(
    row: dict[str, str],
) -> tuple[float, str]:
    deal_year = parse_int(row.get("deal_year"))
    current_official_land_price = parse_float(row.get("current_official_land_price"))
    historical_official_land_price = parse_float(row.get("historical_official_land_price"))
    historical_base_year = parse_int(row.get("historical_land_price_base_year"))
    current_base_year = parse_int(row.get("current_land_price_base_year"))

    if deal_year is None:
        return 1.0, "거래연도 없음"
    if current_base_year is not None and deal_year >= current_base_year:
        return 1.0, f"현재 공시지가 연도({current_base_year})와 동일/이후 거래"
    if not current_official_land_price or current_official_land_price <= 0:
        return 1.0, "기준연도 공시지가 없음"
    if not historical_official_land_price or historical_official_land_price <= 0:
        return 1.0, "거래시점 공시지가 없음"

    ratio = current_official_land_price / historical_official_land_price
    return (
        ratio,
        "공시지가 보정 "
        f"({historical_base_year or deal_year}년 {round(historical_official_land_price):,} → "
        f"{current_base_year or '현재'}년 {round(current_official_land_price):,})",
    )


@tool("get_building_price", args_schema=GetBuildingPriceInputDto)
def get_building_price(
    sigungu_code: str,
    bjdong_code: str,
    bun: str,
    ji: str = "",
    max_candidate_rows: int = 200,
) -> GetBuildingPriceResultDto:
    """특정 건물의 예상 매매가를 계산합니다.

    사용 시점:
    - 특정 건물의 예상 가격, 매입 적정성, 투자 판단을 묻는 질문
    - "이 건물 400억이면 어때?", "비싼 편이야?" 같은 질문

    파라미터:
    - `sigungu_code`, `bjdong_code`, `bun`, `ji`: 대상 건물의 지번 식별자
    - `max_candidate_rows`: 비교사례 후보 수. 특별한 이유가 없으면 기본값 유지

    반환:
    - `target_building`: 대상 건물 기본 정보
    - `selected_stage`: 선택된 비교 단계
    - `candidate_universe_count`: 탐색한 비교 후보 수
    - `comparable_count`: 실제 사용한 비교사례 수
    - `base_estimated_price`, `final_estimated_price`: 보정 전/후 추정가
    - `adjustments`: 적용한 보정 항목
    - `selected_comparables`: 사용된 비교사례 목록
    - `calculation_logs`: 계산 로그
    """
    normalized_gu = normalize_sigungu_code(sigungu_code)
    normalized_dong = normalize_bjdong_code(bjdong_code)
    if not (normalized_gu and normalized_dong and bun):
        return GetBuildingPriceResultDto(error="건물가격 조회에는 sigungu_code, bjdong_code, bun 이 필요합니다.")

    normalized_bun = normalize_lot(bun)
    normalized_ji = normalize_lot(ji, default="0000")
    current_year = date.today().year
    reference_land_price_year = current_year - 1
    max_candidate_rows = max(MIN_REQUIRED_COMPARABLES, min(max_candidate_rows, MAX_CANDIDATE_ROWS))

    log.info(
        f"[툴][get_building_price] 시작 ▶ "
        f"sigungu_code={normalized_gu} bjdong_code={normalized_dong} bun={normalized_bun} ji={normalized_ji} | "
        f"최대후보={max_candidate_rows}건 기준공시지가우선연도={reference_land_price_year}"
    )

    calculation_logs: list[str] = []

    try:
        target_raw = _fetch_target_building(normalized_gu, normalized_dong, normalized_bun, normalized_ji)
    except RuntimeError as exc:
        log.error(f"[툴][get_building_price] STEP 1 ✗ 건물 조회 실패: {exc}")
        return GetBuildingPriceResultDto(error="대상 건물 조회 실패", detail=str(exc))

    if not target_raw:
        return GetBuildingPriceResultDto(
            error="대상 건물을 찾을 수 없습니다.",
            sigungu_code=normalized_gu,
            bjdong_code=normalized_dong,
            bun=normalized_bun,
            ji=normalized_ji,
        )

    target = GetBuildingPriceTargetDto.model_validate(target_raw)

    lat = target.lat
    lng = target.lng
    target_plat_area = target.plat_area
    nearest_station_distance = target.nearest_station_distance
    use_apr_year = target.use_apr_year

    if lat is None or lng is None:
        return GetBuildingPriceResultDto(error="대상 건물의 좌표가 없어 예상 가격을 계산할 수 없습니다.", building=target)
    if not target_plat_area or target_plat_area <= 0:
        return GetBuildingPriceResultDto(error="대상 건물의 대지면적이 없어 예상 가격을 계산할 수 없습니다.", building=target)

    calculation_logs.append(f"대상 건물 조회: {target.bld_nm or target.plat_plc or '이름없음'}")

    try:
        target_zoning_context = _fetch_target_zoning_context(
            normalized_gu,
            normalized_dong,
            normalized_bun,
            normalized_ji,
        )
        target_history_map = _fetch_official_land_price_history([
            _lot_key(normalized_gu, normalized_dong, normalized_bun, normalized_ji)
        ])
    except RuntimeError as exc:
        log.error(f"[툴][get_building_price] STEP 2 ✗ 토지 맥락 조회 실패: {exc}")
        return GetBuildingPriceResultDto(error="대상 건물 토지 맥락 조회 실패", detail=str(exc))

    target_history_rows = target_history_map.get(
        _lot_key(normalized_gu, normalized_dong, normalized_bun, normalized_ji),
        [],
    )
    target_official_land_price_row = _pick_current_official_land_price(
        target_history_rows,
        reference_land_price_year,
    )

    if not target_official_land_price_row:
        return GetBuildingPriceResultDto(
            error=f"대상 건물의 기준 공시지가 정보를 찾을 수 없습니다. (우선 기준연도: {reference_land_price_year})",
            building=target,
        )

    target_land_context = dict(target_zoning_context or {})
    target_land_context["official_land_price"] = target_official_land_price_row.get("price_per_sqm", "")
    target_land_context["base_year"] = target_official_land_price_row.get("base_year", "")
    target_land_context["base_year_month"] = target_official_land_price_row.get("base_year_month", "")

    target_official_land_price = parse_float(target_land_context.get("official_land_price"))
    target_zoning_code_1 = (target_land_context.get("zoning_code_1") or "").strip()
    target_land_price_base_year = parse_int(target_land_context.get("base_year"))
    if not target_official_land_price or target_official_land_price <= 0:
        return GetBuildingPriceResultDto(error="대상 건물의 개별공시지가 값이 올바르지 않습니다.", land_context=target_land_context)
    if not target_zoning_code_1:
        return GetBuildingPriceResultDto(error="대상 건물의 zoning_code_1 정보가 없어 예상 가격을 계산할 수 없습니다.", land_context=target_land_context)

    calculation_logs.append(
        f"대상 토지 맥락 조회: 요청 기준연도 {reference_land_price_year}, 실제 공시지가 연도 {target_land_price_base_year}, "
        f"공시지가 {round(target_official_land_price):,}원/㎡, zoning={target_zoning_code_1}"
    )

    try:
        candidate_rows = _fetch_candidate_universe(
            lat=lat,
            lng=lng,
            min_deal_year=current_year - 10 + 1,
            radius_meters=1000,
            max_rows=max_candidate_rows,
        )
    except RuntimeError as exc:
        log.error(f"[툴][get_building_price] STEP 3 ✗ 거래 universe 조회 실패: {exc}")
        return GetBuildingPriceResultDto(error="건물가격 계산용 거래 universe 조회 실패", detail=str(exc))

    try:
        candidate_history_map = _fetch_official_land_price_history([
            _lot_key_from_row(row) for row in candidate_rows
        ])
        candidate_rows = _attach_official_land_price_context(
            candidate_rows,
            candidate_history_map,
            reference_land_price_year,
        )
    except RuntimeError as exc:
        log.error(f"[툴][get_building_price] STEP 3 ✗ 공시지가 이력 조회 실패: {exc}")
        return GetBuildingPriceResultDto(error="건물가격 계산용 공시지가 이력 조회 실패", detail=str(exc))

    calculation_logs.append(
        f"거래 universe 수집: {len(candidate_rows)}건, 공시지가 이력 lot={len(candidate_history_map)}건"
    )

    target_ctx = {
        "official_land_price": target_official_land_price,
        "zoning_code_1": target_zoning_code_1,
    }
    selected_stage, selected_rows, stage_attempts = _pick_stage(candidate_rows, target_ctx, current_year)

    if not selected_stage:
        calculation_logs.append("단계형 필터 결과: 용도지역 동일 기준 10년/1000m 내 유효 비교사례 3건 미만")
        return GetBuildingPriceResultDto(
            error="비교 가능한 거래 사례가 부족해 예상 가격을 계산할 수 없습니다.",
            building=target,
            candidate_universe_count=len(candidate_rows),
            reference_land_price_year=reference_land_price_year,
            stage_attempts=stage_attempts,
            calculation_logs=calculation_logs,
        )

    calculation_logs.append(
        f"선택 단계: {selected_stage.name} ({selected_stage.recent_years}년, {selected_stage.radius_meters}m)"
    )
    calculation_logs.append(f"선택 단계 비교사례 수: {len(selected_rows)}건")
    required_count = _required_comparables_for_stage(selected_stage)

    comparable_items: list[GetBuildingPriceComparableDto] = []
    unit_prices: list[float] = []
    skipped = 0

    for row in selected_rows:
        deal_amount_krw = parse_float(row.get("deal_amount"))
        land_area, land_area_source = _resolve_comparable_land_area(row)

        if not deal_amount_krw or not land_area or land_area <= 0:
            skipped += 1
            continue

        land_price_ratio, land_price_adjustment_reason = _land_price_adjustment_ratio(row)
        adjusted_deal_amount_krw = deal_amount_krw * land_price_ratio
        adjusted_unit_price = adjusted_deal_amount_krw / land_area

        unit_prices.append(adjusted_unit_price)
        log.debug(
            f"[툴][get_building_price] 비교사례 rtm_id={row.get('rtm_id')} | "
            f"{row.get('deal_year')}-{row.get('deal_month')} | "
            f"원거래 {deal_amount_krw:,.0f}원 | 보정배율 {land_price_ratio:.4f} | "
            f"보정단가 {round(adjusted_unit_price):,}원/㎡ | dist={row.get('distance_m')}m"
        )

        comparable_row = dict(row)
        comparable_row["land_area_used_sqm"] = round(land_area, 2)
        comparable_row["land_area_source"] = land_area_source
        comparable_row["raw_deal_amount"] = KrwAmountDto.from_amount(deal_amount_krw)
        comparable_row["land_price_adjustment_ratio"] = round(land_price_ratio, 6)
        comparable_row["land_price_adjustment_reason"] = land_price_adjustment_reason
        comparable_row["adjusted_deal_amount"] = KrwAmountDto.from_amount(adjusted_deal_amount_krw)
        comparable_row["adjusted_unit_price_per_sqm_krw"] = round(adjusted_unit_price)
        comparable_items.append(GetBuildingPriceComparableDto.model_validate(comparable_row))

    if len(unit_prices) < required_count:
        calculation_logs.append(
            f"선택 단계 내 유효 사례 부족: {len(unit_prices)}건 (스킵 {skipped}건, 최소 {required_count}건)"
        )
        return GetBuildingPriceResultDto(
            error="선택된 조건 내 유효 거래 사례가 부족해 예상 가격을 계산할 수 없습니다.",
            building=target,
            selected_stage=_stage_to_dto(selected_stage),
            comparable_count=len(unit_prices),
            reference_land_price_year=reference_land_price_year,
            calculation_logs=calculation_logs,
        )

    median_unit_price_val = float(median(unit_prices))
    base_estimated_price_krw = target_plat_area * median_unit_price_val

    calculation_logs.append(
        f"공시지가 시점 보정 적용: 기준연도 {reference_land_price_year}, 비교사례 {len(comparable_items)}건"
    )
    calculation_logs.append(
        f"중위 단가: {round(median_unit_price_val):,}원/㎡ "
        f"(보정단가들: {[round(price) for price in unit_prices]})"
    )
    calculation_logs.append(
        f"기본 예상 가격: 대지면적 {target_plat_area:.2f}㎡ × {round(median_unit_price_val):,}원/㎡"
    )

    station_rate, station_reason = _station_adjustment(nearest_station_distance)
    road_rate, road_reason, is_excluded = _road_adjustment(target_land_context.get("road_contact_code"))
    age_rate, age_reason = _age_adjustment(use_apr_year, current_year)
    terrain_rate, terrain_reason = _terrain_shape_adjustment(target_land_context.get("terrain_shape_code"))

    adjustments = [
        GetBuildingPriceAdjustmentDto(type="station_access", rate=round(station_rate, 4), reason=station_reason),
        GetBuildingPriceAdjustmentDto(type="road_contact", rate=round(road_rate, 4), reason=road_reason),
        GetBuildingPriceAdjustmentDto(type="building_age", rate=round(age_rate, 4), reason=age_reason),
        GetBuildingPriceAdjustmentDto(type="terrain_shape", rate=round(terrain_rate, 4), reason=terrain_reason),
    ]

    calculation_logs.append(f"역 접근성 보정: {station_reason} ({station_rate:+.0%})")
    calculation_logs.append(f"도로 접면 보정: {road_reason} ({road_rate:+.0%})")
    calculation_logs.append(f"건축 연식 보정: {age_reason} ({age_rate:+.0%})")
    calculation_logs.append(f"지형 형상 보정: {terrain_reason} ({terrain_rate:+.0%})")

    if is_excluded:
        return GetBuildingPriceResultDto(
            target_building=target,
            excluded=True,
            message="자동 평가 제외 대상입니다.",
        )

    raw_adjustment_rate = station_rate + road_rate + age_rate + terrain_rate
    capped_adjustment_rate = min(0.30, max(-0.40, raw_adjustment_rate))
    final_estimated_price_krw = base_estimated_price_krw * (1 + capped_adjustment_rate)

    calculation_logs.append(f"보정치 합계: {raw_adjustment_rate:+.0%}, 캡 적용 후: {capped_adjustment_rate:+.0%}")
    calculation_logs.append(
        f"최종 예상 가격: {round(base_estimated_price_krw):,}원 × (1 {capped_adjustment_rate:+.0%})"
    )

    log.info(
        f"[툴][get_building_price] 완료 ◀ "
        f"최종 {format_human_krw(final_estimated_price_krw)} "
        f"(기본 {format_human_krw(base_estimated_price_krw)}, 보정 {capped_adjustment_rate:+.0%})"
    )

    return GetBuildingPriceResultDto(
        target_building=target,
        selected_stage=_stage_to_dto(selected_stage),
        reference_land_price_year=reference_land_price_year,
        comparable_count=len(comparable_items),
        # base_estimated_price=KrwAmountDto.from_amount(base_estimated_price_krw),
        final_estimated_price=KrwAmountDto.from_amount(final_estimated_price_krw),
        # adjustments=adjustments,
        selected_comparables=comparable_items,
        calculation_logs=calculation_logs,
        excluded=False,
    )