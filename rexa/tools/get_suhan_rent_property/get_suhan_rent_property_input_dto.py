from pydantic import AliasChoices, BaseModel, Field


class GetSuhanRentPropertyInputDto(BaseModel):
    lat: float | None = Field(default=None, validation_alias=AliasChoices("lat", "latitude"), description="중심 위도. 반경 검색용.")
    lng: float | None = Field(default=None, validation_alias=AliasChoices("lng", "longitude"), description="중심 경도. 반경 검색용.")
    radius_m: float = Field(default=3000, description="반경 검색 거리(m).", gt=0)
    sigungu_code: str = Field(default="", validation_alias=AliasChoices("sigungu_code", "sigungu_cd"), description="5자리 시군구 코드. 주소 검색용.")
    bjdong_code: str = Field(default="", validation_alias=AliasChoices("bjdong_code", "dong_cd"), description="5자리 법정동 코드. 주소 검색용.")
    bun: str = Field(default="", description="지번 본번. 주소 검색용.")
    ji: str = Field(default="", description="지번 부번. 주소 검색용.")
    code: str = Field(default="", description="서안개발 매물 코드. 있으면 코드 단건 검색.")
    rental_area_min: float | None = Field(default=None, description="최소 임대면적(㎡). 평 입력은 ㎡로 환산.")
    rental_area_max: float | None = Field(default=None, description="최대 임대면적(㎡). 평 입력은 ㎡로 환산.")
    exclusive_area_min: float | None = Field(default=None, description="최소 전용면적(㎡). 평 입력은 ㎡로 환산.")
    exclusive_area_max: float | None = Field(default=None, description="최대 전용면적(㎡). 평 입력은 ㎡로 환산.")
    deposit_min: float | None = Field(default=None, description="보증금 최소(원). 만/억 입력은 원으로 변환.")
    deposit_max: float | None = Field(default=None, description="보증금 최대(원). 만/억 입력은 원으로 변환.")
    monthly_rent_min: float | None = Field(default=None, description="월 임대료 최소(원). 만/억 입력은 원으로 변환.")
    monthly_rent_max: float | None = Field(default=None, description="월 임대료 최대(원). 만/억 입력은 원으로 변환.")
    maintenance_fee_min: float | None = Field(default=None, description="관리비 최소(원). 만 입력은 원으로 변환.")
    maintenance_fee_max: float | None = Field(default=None, description="관리비 최대(원). 만 입력은 원으로 변환.")
    min_stn_dist_min: float | None = Field(default=None, description="최인접 역까지 최소 거리(m).")
    min_stn_dist_max: float | None = Field(default=None, description="최인접 역까지 최대 거리(m).")
