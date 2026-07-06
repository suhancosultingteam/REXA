from pydantic import AliasChoices, BaseModel, Field


class SearchCommercialAreaInputDto(BaseModel):
    sigungu_code: str = Field(
        validation_alias=AliasChoices("sigungu_code", "gu_code"),
        description="5자리 시군구 코드. 구 단위 상권 분석용.",
    )
    queries: list[str] = Field(
        description="상권 보고서 검색용 자연어 쿼리 배열. 장소명과 분석 관점을 함께 넣습니다.",
        min_length=1,
    )
