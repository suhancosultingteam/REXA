from pydantic import BaseModel


class GetBuildingRegistryQueryDto(BaseModel):
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None
    mgm_bldrgst_pk: str | None = None
