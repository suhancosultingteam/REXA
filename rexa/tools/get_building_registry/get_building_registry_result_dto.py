from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_building_registry.get_building_registry_building_dto import GetBuildingRegistryBuildingDto
from rexa.tools.get_building_registry.get_building_registry_query_dto import GetBuildingRegistryQueryDto


class GetBuildingRegistryResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None

    # query: GetBuildingRegistryQueryDto | None = None
    building: GetBuildingRegistryBuildingDto | None = None
