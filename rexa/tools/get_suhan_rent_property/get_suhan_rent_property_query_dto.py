from typing import Literal

from pydantic import BaseModel

from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_filters_dto import GetSuhanRentPropertyFiltersDto


class GetSuhanRentPropertyQueryDto(BaseModel):
    search_mode: Literal["radius", "address", "code"] | None = None
    lat: float | None = None
    lng: float | None = None
    radius_m: float | None = None
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
    code: str | None = None
    filters: GetSuhanRentPropertyFiltersDto | None = None
