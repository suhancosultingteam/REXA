from __future__ import annotations

from datetime import date
from statistics import mean, median
from typing import Any

from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._common_dto.stats_dto import MoneyStatsDto, StatsDto
from rexa.tools._utils import (
    parse_float,
    parse_int,
    run_sql,
)
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_input_dto import GetAreaTransactionStatsInputDto
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_query_dto import GetAreaTransactionStatsQueryDto
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_result_dto import GetAreaTransactionStatsResultDto
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_stats_dto import GetAreaTransactionStatsStatsDto
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_transaction_dto import GetAreaTransactionStatsTransactionDto

log = setup_logger()

_SQM_PER_PYEONG = 3.3058


def _pyeong(sqm: float) -> float:
    return sqm / _SQM_PER_PYEONG


def _stats_dto(values: list[float]) -> StatsDto:
    return StatsDto(
        mean=round(mean(values), 2),
        median=round(median(values), 2),

        min=round(min(values), 2),
        max=round(max(values), 2),
        count=len(values),
    )


def _money_stats_dto(values: list[float]) -> MoneyStatsDto:
    return MoneyStatsDto(
        mean=KrwAmountDto.from_amount(mean(values)),
        median=KrwAmountDto.from_amount(median(values)),
        min=KrwAmountDto.from_amount(min(values)),
        max=KrwAmountDto.from_amount(max(values)),
        count=len(values),
    )


@tool(args_schema=GetAreaTransactionStatsInputDto)
def get_area_transaction_stats(
    lat: float,
    lng: float,
    radius_m: float = 1000,
    recent_years: int = 3,
) -> GetAreaTransactionStatsResultDto:
    """특정 좌표 반경 내 거래 통계를 조회합니다.

    사용 시점:
    - "이 근처 거래 시세 어때?", "강남역 근처 평당가 알려줘" 같은 주변 시세 질문

    반환:
    - `query`: 중심 좌표와 조회 반경
    - `transaction_count`: 유효 거래 수
    - `stats`: 거래금액, 면적, 평당가 통계
    - `transactions`: 샘플 거래 목록
    """
    current_year = date.today().year
    min_deal_year = current_year - recent_years + 1

    log.info(
        f"[툴][get_area_transaction_stats] 시작 ▶ "
        f"lat={lat} lng={lng} radius={radius_m}m recent_years={recent_years} "
        f"(deal_year>={min_deal_year})"
    )

    sql_query = f"""
    SELECT
        t.id AS rtm_id,
        t.deal_year,
        t.deal_month,
        t.deal_amount,
        t.plottage_ar,
        t.building_ar,
        b.plat_area,
        b.tot_area,
        b.bld_nm,
        b.main_purps_cd_nm,
        b.new_plat_plc,
        b.plat_plc,
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
    WHERE b.geog IS NOT NULL
      AND t.deal_amount IS NOT NULL
      AND t.deal_year >= {min_deal_year}
      AND ST_DWithin(
            b.geog,
            ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography,
            {radius_m}
          )
    ORDER BY distance_m ASC, t.deal_year DESC, t.deal_month DESC, t.id DESC
    LIMIT 100
    """

    try:
        rows = run_sql(sql_query)
    except RuntimeError as exc:
        log.error(f"[툴][get_area_transaction_stats] DB 조회 실패 | {exc}")
        return GetAreaTransactionStatsResultDto(error="거래 통계 조회 실패", detail=str(exc))

    if not rows:
        log.info("[툴][get_area_transaction_stats] 결과 없음")
        return GetAreaTransactionStatsResultDto(
            error="해당 반경 내 거래 데이터가 없습니다.",
            radius_m=radius_m,
            recent_years=recent_years,
        )

    # 유효 거래만 추출
    deal_amounts_krw: list[float] = []
    land_areas: list[float] = []
    total_areas: list[float] = []
    land_price_per_pyeong_krw: list[float] = []
    building_price_per_pyeong_krw: list[float] = []
    transactions: list[GetAreaTransactionStatsTransactionDto] = []

    for row in rows:
        deal_amount_krw = parse_float(row.get("deal_amount"))
        if not deal_amount_krw:
            continue

        land_area = parse_float(row.get("plottage_ar")) or parse_float(row.get("plat_area"))
        total_area = parse_float(row.get("building_ar")) or parse_float(row.get("tot_area"))

        tx = GetAreaTransactionStatsTransactionDto(
            rtm_id=row.get("rtm_id"),
            deal_year=row.get("deal_year"),
            deal_month=row.get("deal_month"),
            deal_amount=KrwAmountDto.from_amount(deal_amount_krw),
            address=row.get("new_plat_plc") or row.get("plat_plc"),
            bld_nm=row.get("bld_nm"),
            use=row.get("main_purps_cd_nm"),
            distance_m=parse_int(row.get("distance_m")),
        )

        deal_amounts_krw.append(deal_amount_krw)

        if land_area and land_area > 0:
            tx.land_area_sqm = round(land_area, 2)
            tx.land_area_pyeong = round(_pyeong(land_area), 2)
            land_areas.append(land_area)
            ppu = deal_amount_krw / _pyeong(land_area)
            tx.land_price_per_pyeong_krw = round(ppu)
            tx.land_price_per_pyeong = KrwAmountDto.from_amount(ppu)
            land_price_per_pyeong_krw.append(ppu)

        if total_area and total_area > 0:
            tx.total_area_sqm = round(total_area, 2)
            tx.total_area_pyeong = round(_pyeong(total_area), 2)
            total_areas.append(total_area)
            ppu = deal_amount_krw / _pyeong(total_area)
            tx.building_price_per_pyeong_krw = round(ppu)
            tx.building_price_per_pyeong = KrwAmountDto.from_amount(ppu)
            building_price_per_pyeong_krw.append(ppu)

        transactions.append(tx)

    if not deal_amounts_krw:
        return GetAreaTransactionStatsResultDto(error="유효한 거래 데이터가 없습니다.")

    stats = GetAreaTransactionStatsStatsDto(
        deal_amount=_money_stats_dto(deal_amounts_krw),
    )
    if land_areas:
        stats.land_area_sqm = _stats_dto(land_areas)
        stats.land_area_pyeong = _stats_dto([_pyeong(v) for v in land_areas])
    if total_areas:
        stats.total_area_sqm = _stats_dto(total_areas)
        stats.total_area_pyeong = _stats_dto([_pyeong(v) for v in total_areas])
    if land_price_per_pyeong_krw:
        stats.land_price_per_pyeong_krw = _stats_dto(land_price_per_pyeong_krw)
        stats.land_price_per_pyeong = _money_stats_dto(land_price_per_pyeong_krw)
    if building_price_per_pyeong_krw:
        stats.building_price_per_pyeong_krw = _stats_dto(building_price_per_pyeong_krw)
        stats.building_price_per_pyeong = _money_stats_dto(building_price_per_pyeong_krw)

    log.info(
        f"[툴][get_area_transaction_stats] 완료 ▶ 유효거래 {len(transactions)}건 | "
        f"거래금액 중위 {stats.deal_amount.median.human if stats.deal_amount else '-'} | "
        f"대지평당가 중위 {stats.land_price_per_pyeong.median.human if stats.land_price_per_pyeong else '-'} | "
        f"건물평당가 중위 {stats.building_price_per_pyeong.median.human if stats.building_price_per_pyeong else '-'}"
    )

    return GetAreaTransactionStatsResultDto(
        query=GetAreaTransactionStatsQueryDto(
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            recent_years=recent_years,
            min_deal_year=min_deal_year,
        ),
        transaction_count=len(transactions),
        stats=stats
    )
