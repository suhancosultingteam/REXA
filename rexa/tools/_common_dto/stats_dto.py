from pydantic import BaseModel

from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto


class StatsDto(BaseModel):
    mean: float
    median: float
    min: float
    max: float
    count: int


class MoneyStatsDto(BaseModel):
    mean: KrwAmountDto
    median: KrwAmountDto
    min: KrwAmountDto
    max: KrwAmountDto
    count: int
