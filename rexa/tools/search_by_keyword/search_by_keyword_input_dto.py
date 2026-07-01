from pydantic import BaseModel, Field


class SearchByKeywordInputDto(BaseModel):
    keyword: str = Field(
        description="건물명, 역명, 랜드마크, 상호명 같은 고유명사 장소. 예: '경복궁', '강남역', '센터필드', '코엑스'",
    )