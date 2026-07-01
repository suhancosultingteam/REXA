from pydantic import BaseModel


class GetSuhanRentPropertyFiltersDto(BaseModel):
    rental_area_min: float | None = None
    rental_area_max: float | None = None
    exclusive_area_min: float | None = None
    exclusive_area_max: float | None = None
    deposit_min: float | None = None
    deposit_max: float | None = None
    monthly_rent_min: float | None = None
    monthly_rent_max: float | None = None
    maintenance_fee_min: float | None = None
    maintenance_fee_max: float | None = None
    min_stn_dist_min: float | None = None
    min_stn_dist_max: float | None = None
