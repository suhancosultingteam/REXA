from pydantic import AliasChoices, BaseModel, Field


class GetBuildingPriceInputDto(BaseModel):
    sigungu_code: str = Field(validation_alias=AliasChoices("sigungu_code", "gu_code"), description="5자리 시군구 코드.")
    bjdong_code: str = Field(validation_alias=AliasChoices("bjdong_code", "dong_code"), description="5자리 법정동 코드.")
    bun: str = Field(description="지번 본번.")
    ji: str = Field(default="", description="지번 부번. 없으면 빈 문자열로 둘 수 있습니다.")
    max_candidate_rows: int = Field(
        default=200,
        description="비교사례로 탐색할 최대 후보 거래 수. 보통 기본값을 유지합니다.",
        ge=3,
        le=500,
    )
