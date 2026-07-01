from __future__ import annotations

from pydantic import BaseModel


class AddressLookupResultDto(BaseModel):
    error: str | None = None

    keyword: str | None = None
    origin: str | None = None
    query: str | None = None
    fullname: str | None = None
    sigungu_name: str | None = None
    sigungu_code: str | None = None
    bjdong_name: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
    lat: float | None = None
    lng: float | None = None

    candidates: list["AddressLookupResultDto"] | None = None


AddressLookupResultDto.model_rebuild()
