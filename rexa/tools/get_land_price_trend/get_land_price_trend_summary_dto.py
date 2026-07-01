from pydantic import BaseModel


class GetLandPriceTrendSummaryDto(BaseModel):
    years: int
    start_year: int | None = None
    end_year: int | None = None
    start_price_per_sqm: int | None = None
    end_price_per_sqm: int | None = None
    total_change: int | None = None
    total_rate: float | None = None
    cagr: float | None = None
