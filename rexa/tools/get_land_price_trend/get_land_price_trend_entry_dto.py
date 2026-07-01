from pydantic import BaseModel


class GetLandPriceTrendEntryDto(BaseModel):
    year: int | None = None
    price_per_sqm: float | None = None
    parcel_type_name: str | None = None
    yoy_change: int | None = None
    yoy_rate: float | None = None
