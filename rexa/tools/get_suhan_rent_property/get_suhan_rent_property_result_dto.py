from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_listing_dto import GetSuhanRentPropertyListingDto
from rexa.tools.get_suhan_rent_property.get_suhan_rent_property_query_dto import GetSuhanRentPropertyQueryDto


class GetSuhanRentPropertyResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    query: GetSuhanRentPropertyQueryDto | None = None
    count: int | None = None
    listings: list[GetSuhanRentPropertyListingDto] | None = None
