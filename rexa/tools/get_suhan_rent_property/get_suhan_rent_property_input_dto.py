from pydantic import AliasChoices, BaseModel, Field


class GetSuhanRentPropertyInputDto(BaseModel):
    lat: float | None = Field(default=None, validation_alias=AliasChoices("lat", "latitude"), description="중심 위도. 반경 검색 시 사용합니다.")
    lng: float | None = Field(default=None, validation_alias=AliasChoices("lng", "longitude"), description="중심 경도. 반경 검색 시 사용합니다.")
    radius_m: float = Field(default=3000, description="좌표 반경 검색 반경(m).", gt=0)
    sigungu_code: str = Field(default="", validation_alias=AliasChoices("sigungu_code", "sigungu_cd"), description="5자리 시군구 코드. 주소 기반 검색 시 사용합니다.")
    bjdong_code: str = Field(default="", validation_alias=AliasChoices("bjdong_code", "dong_cd"), description="5자리 법정동 코드. 주소 기반 검색 시 사용합니다.")
    bun: str = Field(default="", description="지번 본번. 주소 기반 검색 시 사용합니다.")
    ji: str = Field(default="", description="지번 부번. 주소 기반 검색 시 사용합니다.")
    code: str = Field(default="", description="서안개발 매물 코드. 있으면 코드로 단건 검색합니다.")
    rental_area_min: float | None = Field(default=None, description="최소 임대면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 30평 -> 99.174")
    rental_area_max: float | None = Field(default=None, description="최대 임대면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 100평 이내 -> 330.58")
    exclusive_area_min: float | None = Field(default=None, description="최소 전용면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 30평 이상 -> 99.174")
    exclusive_area_max: float | None = Field(default=None, description="최대 전용면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 100평 이내 -> 330.58")
    deposit_min: float | None = Field(default=None, description="보증금 최소 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 5000만 -> 50000000, 1억 -> 100000000, 5억 -> 500000000")
    deposit_max: float | None = Field(default=None, description="보증금 최대 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 5000만 -> 50000000, 1억 -> 100000000, 5억 -> 500000000")
    monthly_rent_min: float | None = Field(default=None, description="월 임대료 최소 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 500만 -> 5000000, 5000만 -> 50000000, 1억 -> 100000000")
    monthly_rent_max: float | None = Field(default=None, description="월 임대료 최대 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 500만 -> 5000000, 5000만 -> 50000000, 1억 -> 100000000")
    maintenance_fee_min: float | None = Field(default=None, description="관리비 최소 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 100만 -> 1000000, 50만 -> 500000")
    maintenance_fee_max: float | None = Field(default=None, description="관리비 최대 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 100만 -> 1000000, 50만 -> 500000")
    min_stn_dist_min: float | None = Field(default=None, description="최인접 역까지 거리 최소 조건 값(m).")
    min_stn_dist_max: float | None = Field(default=None, description="최인접 역까지 거리 최대 조건 값(m).")
