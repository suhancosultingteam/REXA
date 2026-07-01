from typing import Any

from pydantic import BaseModel

from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._utils import KUMHA_BUILDING_CODE, format_human_krw, mask_jibun_address, mask_road_address, parse_float, parse_int


class _AddressDto(BaseModel):
    jibun: str | None = None
    road: str | None = None
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None


class _AreaDto(BaseModel):
    land_sqm: float | None = None
    total_sqm: float | None = None


class _LocationDto(BaseModel):
    lat: float | None = None
    lng: float | None = None
    distance_m: int | None = None


class _StationDto(BaseModel):
    name: str | None = None
    distance_m: float | None = None


class GetSuhanPropertyListingDto(BaseModel):
    id: int | None = None
    name: str | None = None
    code: str | None = None
    base_url: str | None = None
    address: _AddressDto | None = None
    price: KrwAmountDto | None = None
    area: _AreaDto | None = None
    floors: int | None = None
    location: _LocationDto | None = None
    nearest_station: _StationDto | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "GetSuhanPropertyListingDto":
        price_krw = parse_int(row.get("price"))
        code = row.get("code")
        should_mask_address = code != KUMHA_BUILDING_CODE
        return cls(
            id=parse_int(row.get("id")),
            name=row.get("name"),
            code=code,
            base_url=row.get("base_url"),
            address=_AddressDto(
                jibun=mask_jibun_address(row.get("jibun_addr")) if should_mask_address else row.get("jibun_addr"),
                road=mask_road_address(row.get("road_addr")) if should_mask_address else row.get("road_addr"),
                sigungu_code=row.get("sigungu_code"),
                bjdong_code=row.get("bjdong_code"),
                bun=row.get("bun"),
                ji=row.get("ji"),
            ),
            price=KrwAmountDto(krw=price_krw, human=format_human_krw(price_krw)),
            area=_AreaDto(
                land_sqm=parse_float(row.get("land_area")),
                total_sqm=parse_float(row.get("total_area")),
            ),
            floors=parse_int(row.get("floors")),
            location=_LocationDto(
                lat=parse_float(row.get("lat")),
                lng=parse_float(row.get("lng")),
                distance_m=parse_int(row.get("distance_m")),
            ),
            nearest_station=_StationDto(
                name=row.get("min_stn_name"),
                distance_m=parse_float(row.get("min_stn_dist")),
            ),
        )
