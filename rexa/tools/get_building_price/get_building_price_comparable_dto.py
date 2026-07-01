from pydantic import BaseModel, ConfigDict, field_validator

from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._utils import parse_float, parse_int


class GetBuildingPriceComparableDto(BaseModel):
    model_config = ConfigDict(extra="allow")

    rtm_id: str | None = None
    deal_year: str | None = None
    deal_month: str | None = None
    deal_day: str | None = None
    deal_amount: str | None = None
    plottage_ar: float | None = None
    building_ar: float | None = None
    mgm_bldrgst_pk: str | None = None
    plat_plc: str | None = None
    new_plat_plc: str | None = None
    bld_nm: str | None = None
    main_purps_cd_nm: str | None = None
    plat_area: float | None = None
    tot_area: float | None = None
    use_apr_year: int | None = None
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
    zoning_code_1: str | None = None
    zoning_name_1: str | None = None
    road_contact_code: str | None = None
    road_contact_name: str | None = None
    current_land_area: float | None = None
    distance_m: int | None = None
    current_official_land_price: str | None = None
    current_land_price_base_year: str | None = None
    current_land_price_base_month: str | None = None
    historical_official_land_price: str | None = None
    historical_land_price_base_year: str | None = None
    historical_land_price_base_month: str | None = None
    land_area_used_sqm: float | None = None
    land_area_source: str | None = None
    raw_deal_amount: KrwAmountDto | None = None
    land_price_adjustment_ratio: float | None = None
    land_price_adjustment_reason: str | None = None
    adjusted_deal_amount: KrwAmountDto | None = None
    adjusted_unit_price_per_sqm_krw: int | None = None

    @field_validator("plottage_ar", "building_ar", "plat_area", "tot_area", "current_land_area", "land_area_used_sqm", mode="before")
    @classmethod
    def _to_float(cls, v: object) -> float | None:
        return parse_float(v)

    @field_validator("use_apr_year", "distance_m", "adjusted_unit_price_per_sqm_krw", mode="before")
    @classmethod
    def _to_int(cls, v: object) -> int | None:
        return parse_int(v)

    @field_validator("raw_deal_amount", "adjusted_deal_amount", mode="before")
    @classmethod
    def _to_krw(cls, v: object) -> KrwAmountDto | None:
        if v is None or v == "":
            return None
        if isinstance(v, (dict, KrwAmountDto)):
            return KrwAmountDto.model_validate(v) if isinstance(v, dict) else v
        return KrwAmountDto.from_amount(v)
