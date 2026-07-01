from pydantic import AliasChoices, BaseModel, Field


class GetSuhanPropertyInputDto(BaseModel):
    lat: float | None = Field(default=None, validation_alias=AliasChoices("lat", "latitude"), description="중심 위도. 반경 검색 시 사용합니다.")
    lng: float | None = Field(default=None, validation_alias=AliasChoices("lng", "longitude"), description="중심 경도. 반경 검색 시 사용합니다.")
    radius_m: float = Field(default=3000, description="좌표 반경 검색 반경(m).", gt=0)
    sigungu_code: str = Field(default="", validation_alias=AliasChoices("sigungu_code", "sigungu_cd"), description="5자리 시군구 코드. 주소 기반 검색 시 사용합니다.")
    bjdong_code: str = Field(default="", validation_alias=AliasChoices("bjdong_code", "dong_cd"), description="5자리 법정동 코드. 주소 기반 검색 시 사용합니다.")
    bun: str = Field(default="", description="지번 본번. 주소 기반 검색 시 사용합니다.")
    ji: str = Field(default="", description="지번 부번. 주소 기반 검색 시 사용합니다.")
    code: str = Field(default="", description="서안개발 매물 코드. 있으면 코드로 단건 검색합니다.")
    land_area_min: float | None = Field(default=None, description="최소 대지면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 30평 -> 99.174")
    land_area_max: float | None = Field(default=None, description="최대 대지면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 100평 이내 -> 330.58")
    total_area_min: float | None = Field(default=None, description="최소 연면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 30평 이상 -> 99.174")
    total_area_max: float | None = Field(default=None, description="최대 연면적(㎡). 사용자가 평으로 말하면 ㎡로 환산해 넣습니다. 예: 100평 이내 -> 330.58")
    price_min: float | None = Field(default=None, description="매물 가격 최소 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 100억 -> 10000000000, 50억 -> 5000000000, 5000만 -> 50000000")
    price_max: float | None = Field(default=None, description="매물 가격 최대 조건 값(원). 단위 변환: 1만 = 10,000 (0이 4개), 1억 = 100,000,000 (0이 8개). 절대 만/억 단위 숫자를 그대로 넣지 마세요. 예: 200억 -> 20000000000, 50억 -> 5000000000, 5000만 -> 50000000")
    min_stn_dist_min: float | None = Field(default=None, description="최인접 역까지 거리 최소 조건 값(m).")
    min_stn_dist_max: float | None = Field(default=None, description="최인접 역까지 거리 최대 조건 값(m).")
