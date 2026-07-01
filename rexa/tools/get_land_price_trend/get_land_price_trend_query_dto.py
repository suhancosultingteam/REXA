from pydantic import BaseModel


class GetLandPriceTrendQueryDto(BaseModel):
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
