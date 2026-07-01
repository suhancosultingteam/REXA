from pydantic import BaseModel, Field


class SearchByAddressInputDto(BaseModel):
    address: str = Field(
        description="지번 주소, 도로명 주소, 행정동/법정동 이름. 예: '세종로 1-1', '강남대로 123', '역삼동', '청담동'",
    )
