from pydantic import AliasChoices, BaseModel, Field


class GetLandPriceInputDto(BaseModel):
    sigungu_code: str = Field(validation_alias=AliasChoices("sigungu_code", "gu_code"), description="5자리 시군구 코드.")
    bjdong_code: str = Field(validation_alias=AliasChoices("bjdong_code", "dong_code"), description="5자리 법정동 코드.")
    bun: str = Field(description="지번 본번.")
    ji: str = Field(default="", description="지번 부번. 없으면 빈 문자열로 둘 수 있습니다.")
    base_year: int | None = Field(default=None, description="기준 연도. 지정하면 해당 연도 이하의 최신 공시지가를 반환합니다.")
