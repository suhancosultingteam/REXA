from typing import Literal

from rexa.tools._common_dto.tool_result_base import ToolResultBase


class GenericRealEstateQAResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None

    question: str | None = None
    answer: str | None = None
    source: Literal["llm_general_knowledge"] | None = None
