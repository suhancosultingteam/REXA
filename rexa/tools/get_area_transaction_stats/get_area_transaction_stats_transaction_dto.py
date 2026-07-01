from pydantic import BaseModel

from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto


class GetAreaTransactionStatsTransactionDto(BaseModel):
    rtm_id: str | None = None
    deal_year: str | None = None
    deal_month: str | None = None
    deal_amount: KrwAmountDto | None = None
    address: str | None = None
    bld_nm: str | None = None
    use: str | None = None
    distance_m: int | None = None
    land_area_sqm: float | None = None
    land_area_pyeong: float | None = None
    land_price_per_pyeong_krw: int | None = None
    land_price_per_pyeong: KrwAmountDto | None = None
    total_area_sqm: float | None = None
    total_area_pyeong: float | None = None
    building_price_per_pyeong_krw: int | None = None
    building_price_per_pyeong: KrwAmountDto | None = None
