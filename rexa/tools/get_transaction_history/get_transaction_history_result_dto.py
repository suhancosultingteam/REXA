from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_transaction_history.get_transaction_history_query_dto import GetTransactionHistoryQueryDto
from rexa.tools.get_transaction_history.get_transaction_history_transaction_dto import GetTransactionHistoryTransactionDto


class GetTransactionHistoryResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    query: GetTransactionHistoryQueryDto | None = None
    count: int | None = None
    transactions: list[GetTransactionHistoryTransactionDto] | None = None
