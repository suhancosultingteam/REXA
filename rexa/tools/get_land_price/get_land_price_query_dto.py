from pydantic import BaseModel


class GetLandPriceQueryDto(BaseModel):
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
    base_year: int | None = None
