from pydantic import BaseModel, field_validator

from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._utils import parse_int


class GetLandPriceLatestDto(BaseModel):
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    main_lot_number: str | None = None
    sub_lot_number: str | None = None
    base_year: int | None = None
    base_year_month: str | None = None
    price_per_sqm: KrwAmountDto | None = None
    parcel_type_name: str | None = None

    @field_validator("base_year", mode="before")
    @classmethod
    def _to_int(cls, v: object) -> int | None:
        return parse_int(v)

    @field_validator("price_per_sqm", mode="before")
    @classmethod
    def _to_krw(cls, v: object) -> KrwAmountDto | None:
        if v is None or v == "":
            return None
        if isinstance(v, KrwAmountDto):
            return v
        return KrwAmountDto.from_amount(v)
