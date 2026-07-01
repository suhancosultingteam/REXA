from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_land_price.get_land_price_latest_dto import GetLandPriceLatestDto
from rexa.tools.get_land_price.get_land_price_query_dto import GetLandPriceQueryDto


class GetLandPriceResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    # error 보조 필드 (error_result 호환)
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None

    query: GetLandPriceQueryDto | None = None
    latest: GetLandPriceLatestDto | None = None
