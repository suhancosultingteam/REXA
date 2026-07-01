from pydantic import BaseModel, Field


class GetBuildingRegistryInputDto(BaseModel):
    sigungu_code: str = Field(description="5자리 시군구 코드.")
    bjdong_code: str = Field(description="5자리 법정동 코드.")
    bun: str = Field(description="지번 본번.")
    ji: str = Field(default="", description="지번 부번. 없으면 빈 문자열 또는 0000으로 전달합니다.")
    mgm_bldrgst_pk: str | None = Field(default=None, description="건축물대장 관리 PK. 있으면 동일 주소 내 특정 건물을 단건으로 고정합니다.")
