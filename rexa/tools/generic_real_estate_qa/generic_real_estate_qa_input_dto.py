from pydantic import BaseModel, Field


class GenericRealEstateQAInputDto(BaseModel):
    question: str = Field(description="조회 데이터 없이 설명 가능한 일반 부동산 개념 질문.")
