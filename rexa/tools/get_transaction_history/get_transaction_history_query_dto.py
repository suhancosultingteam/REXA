from pydantic import BaseModel


class GetTransactionHistoryQueryDto(BaseModel):
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_meters: int | None = None
    recent_years: int | None = None
    limit: int | None = None
