from pydantic import BaseModel


class GetAreaTransactionStatsQueryDto(BaseModel):
    lat: float | None = None
    lng: float | None = None
    radius_m: float | None = None
    recent_years: int | None = None
    min_deal_year: int | None = None
