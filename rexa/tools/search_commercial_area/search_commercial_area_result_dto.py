from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.search_commercial_area.search_commercial_area_chunk_dto import SearchCommercialAreaChunkDto


class SearchCommercialAreaResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    status: int | None = None
    base_url: str | None = None

    sigungu_code: str | None = None
    district: str | None = None
    queries: list[str] | None = None
    count: int | None = None
    chunks: list[SearchCommercialAreaChunkDto] | None = None
