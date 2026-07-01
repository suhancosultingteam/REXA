from pydantic import BaseModel


class GetBuildingPriceStageDto(BaseModel):
    stage: str | None = None
    recent_years: int | None = None
    radius_meters: int | None = None
    require_same_zoning: bool | None = None
    require_land_price_band: bool | None = None
