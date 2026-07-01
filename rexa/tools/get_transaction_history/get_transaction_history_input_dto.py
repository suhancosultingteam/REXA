from pydantic import AliasChoices, BaseModel, Field


class GetTransactionHistoryInputDto(BaseModel):
    sigungu_code: str = Field(default="", validation_alias=AliasChoices("sigungu_code", "gu_code"), description="5자리 시군구 코드. 주소 기반 조회 시 사용합니다.")
    bjdong_code: str = Field(default="", validation_alias=AliasChoices("bjdong_code", "dong_code"), description="5자리 법정동 코드. 주소 기반 조회 시 사용합니다.")
    bun: str = Field(default="", description="지번 본번. 주소 기반 조회 시 사용합니다.")
    ji: str = Field(default="", description="지번 부번. 없으면 빈 문자열 또는 0000입니다.")
    lat: float | None = Field(default=None, description="위도. 좌표 반경 조회 시 사용합니다.")
    lng: float | None = Field(default=None, description="경도. 좌표 반경 조회 시 사용합니다.")
    radius_meters: int = Field(default=1000, description="좌표 조회 반경(m).", ge=1, le=5000)
    recent_years: int = Field(default=3, description="최근 몇 년의 거래만 볼지 지정합니다.", ge=1, le=30)
    limit: int = Field(default=10, description="최대 반환 거래 건수.", ge=1, le=100)
