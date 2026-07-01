from pydantic import BaseModel, field_validator

from rexa.tools._utils import parse_float, parse_int


class GetBuildingRegistryBuildingDto(BaseModel):
    mgm_bldrgst_pk: str | None = None
    plat_plc: str | None = None
    new_plat_plc: str | None = None
    bld_nm: str | None = None
    dong_nm: str | None = None
    main_purps_cd_nm: str | None = None
    strct_cd_nm: str | None = None
    plat_area: float | None = None
    arch_area: float | None = None
    tot_area: float | None = None
    bc_rat: float | None = None
    vl_rat: float | None = None
    grnd_flr_cnt: int | None = None
    ugrnd_flr_cnt: int | None = None
    hhld_cnt: int | None = None
    fmly_cnt: int | None = None
    ho_cnt: int | None = None
    use_apr_day: str | None = None
    use_apr_year: str | None = None
    lat: float | None = None
    lng: float | None = None
    distance_m: int | None = None

    @field_validator("plat_area", "arch_area", "tot_area", "bc_rat", "vl_rat", "lat", "lng", mode="before")
    @classmethod
    def _to_float(cls, v: object) -> float | None:
        return parse_float(v)

    @field_validator("grnd_flr_cnt", "ugrnd_flr_cnt", "hhld_cnt", "fmly_cnt", "ho_cnt", "distance_m", mode="before")
    @classmethod
    def _to_int(cls, v: object) -> int | None:
        return parse_int(v)
