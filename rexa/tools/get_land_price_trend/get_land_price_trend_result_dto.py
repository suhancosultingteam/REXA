from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_land_price_trend.get_land_price_trend_entry_dto import GetLandPriceTrendEntryDto
from rexa.tools.get_land_price_trend.get_land_price_trend_query_dto import GetLandPriceTrendQueryDto
from rexa.tools.get_land_price_trend.get_land_price_trend_summary_dto import GetLandPriceTrendSummaryDto


class GetLandPriceTrendResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    # error 보조 필드
    sigungu_code: str | None = None
    bjdong_code: str | None = None
    bun: str | None = None
    ji: str | None = None

    query: GetLandPriceTrendQueryDto | None = None
    trend: list[GetLandPriceTrendEntryDto] | None = None
    summary: GetLandPriceTrendSummaryDto | None = None
