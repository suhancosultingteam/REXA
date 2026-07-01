from pydantic import AliasChoices, BaseModel, Field


class GetAreaTransactionStatsInputDto(BaseModel):
    lat: float = Field(validation_alias=AliasChoices("lat", "latitude"), description="중심 위도.")
    lng: float = Field(validation_alias=AliasChoices("lng", "longitude"), description="중심 경도.")
    radius_m: float = Field(default=1000, description="반경(m).", gt=0)
    recent_years: int = Field(default=3, description="최근 몇 년의 거래를 볼지 지정합니다.", ge=1, le=30)
