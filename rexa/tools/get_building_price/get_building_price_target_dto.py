from pydantic import BaseModel, field_validator

from rexa.tools._utils import parse_float, parse_int


class GetBuildingPriceTargetDto(BaseModel):
    mgm_bldrgst_pk: str | None = None
    plat_plc: str | None = None
    new_plat_plc: str | None = None
    bld_nm: str | None = None
    main_purps_cd_nm: str | None = None
    plat_gb_cd: str | None = None
    plat_area: float | None = None
    tot_area: float | None = None
    use_apr_year: int | None = None
    nearest_station_distance: float | None = None
    lat: float | None = None
    lng: float | None = None

    @field_validator("plat_area", "tot_area", "nearest_station_distance", "lat", "lng", mode="before")
    @classmethod
    def _to_float(cls, v: object) -> float | None:
        return parse_float(v)

    @field_validator("use_apr_year", mode="before")
    @classmethod
    def _to_int(cls, v: object) -> int | None:
        return parse_int(v)
