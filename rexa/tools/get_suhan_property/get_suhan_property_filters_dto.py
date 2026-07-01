from pydantic import BaseModel


class GetSuhanPropertyFiltersDto(BaseModel):
    land_area_min: float | None = None
    land_area_max: float | None = None
    total_area_min: float | None = None
    total_area_max: float | None = None
    price_min: float | None = None
    price_max: float | None = None
    min_stn_dist_min: float | None = None
    min_stn_dist_max: float | None = None
