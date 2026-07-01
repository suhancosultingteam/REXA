from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_query_dto import GetAreaTransactionStatsQueryDto
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_stats_dto import GetAreaTransactionStatsStatsDto
from rexa.tools.get_area_transaction_stats.get_area_transaction_stats_transaction_dto import GetAreaTransactionStatsTransactionDto


class GetAreaTransactionStatsResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    # error 보조 필드
    radius_m: float | None = None
    recent_years: int | None = None

    query: GetAreaTransactionStatsQueryDto | None = None
    transaction_count: int | None = None
    stats: GetAreaTransactionStatsStatsDto | None = None
    transactions: list[GetAreaTransactionStatsTransactionDto] | None = None
