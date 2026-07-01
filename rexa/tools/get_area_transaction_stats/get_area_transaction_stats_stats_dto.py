from pydantic import BaseModel

from rexa.tools._common_dto.stats_dto import MoneyStatsDto, StatsDto


class GetAreaTransactionStatsStatsDto(BaseModel):
    deal_amount: MoneyStatsDto | None = None
    land_area_sqm: StatsDto | None = None
    land_area_pyeong: StatsDto | None = None
    total_area_sqm: StatsDto | None = None
    total_area_pyeong: StatsDto | None = None
    land_price_per_pyeong_krw: StatsDto | None = None
    land_price_per_pyeong: MoneyStatsDto | None = None
    building_price_per_pyeong_krw: StatsDto | None = None
    building_price_per_pyeong: MoneyStatsDto | None = None
