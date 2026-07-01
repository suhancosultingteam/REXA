from typing import Any

from pydantic import BaseModel, field_validator

from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._utils import parse_float, parse_int


class GetTransactionHistoryTransactionDto(BaseModel):
    rtm_id: str | None = None
    deal_year: str | None = None
    deal_month: str | None = None
    deal_day: str | None = None
    deal_amount: KrwAmountDto | None = None
    building_use: str | None = None
    building_type: str | None = None
    land_use: str | None = None
    plottage_ar: float | None = None
    building_ar: float | None = None
    floor: int | None = None
    sigungu_code: str | None = None
    sigungu_name: str | None = None
    bjdong_code: str | None = None
    bjdong_name: str | None = None
    jibun: str | None = None
    mgm_bldrgst_pk: str | None = None
    plat_plc: str | None = None
    new_plat_plc: str | None = None
    bld_nm: str | None = None
    lat: float | None = None
    lng: float | None = None
    match_method: str | None = None
    confidence: float | str | None = None
    area_diff_pct: float | None = None
    year_diff: int | None = None
    distance_m: int | None = None

    @field_validator("deal_amount", mode="before")
    @classmethod
    def _to_krw(cls, v: object) -> KrwAmountDto | None:
        if v is None or v == "":
            return None
        if isinstance(v, KrwAmountDto):
            return v
        return KrwAmountDto.from_amount(v)

    @field_validator("plottage_ar", "building_ar", "lat", "lng", "area_diff_pct", mode="before")
    @classmethod
    def _to_float(cls, v: object) -> float | None:
        return parse_float(v)

    @field_validator("floor", "year_diff", "distance_m", mode="before")
    @classmethod
    def _to_int(cls, v: object) -> int | None:
        return parse_int(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def _to_float_or_str(cls, v: object) -> float | str | None:
        if v in (None, ""):
            return None
        try:
            return parse_float(v)
        except (TypeError, ValueError):
            return str(v)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "GetTransactionHistoryTransactionDto":
        return cls.model_validate(row)
