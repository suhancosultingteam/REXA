from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_suhan_property.get_suhan_property_listing_dto import GetSuhanPropertyListingDto
from rexa.tools.get_suhan_property.get_suhan_property_query_dto import GetSuhanPropertyQueryDto


class GetSuhanPropertyResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    query: GetSuhanPropertyQueryDto | None = None
    count: int | None = None
    listings: list[GetSuhanPropertyListingDto] | None = None
