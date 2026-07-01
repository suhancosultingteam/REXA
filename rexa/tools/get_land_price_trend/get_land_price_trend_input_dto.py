from pydantic import AliasChoices, BaseModel, Field


class GetLandPriceTrendInputDto(BaseModel):
    sigungu_code: str = Field(validation_alias=AliasChoices("sigungu_code", "gu_code"), description="5자리 시군구 코드.")
    bjdong_code: str = Field(validation_alias=AliasChoices("bjdong_code", "dong_code"), description="5자리 법정동 코드.")
    bun: str = Field(description="지번 본번.")
    ji: str = Field(default="", description="지번 부번.")
