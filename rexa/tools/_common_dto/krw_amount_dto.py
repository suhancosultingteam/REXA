from pydantic import BaseModel

from rexa.tools._utils import format_human_krw, parse_float


class KrwAmountDto(BaseModel):
    krw: int | None = None
    human: str | None = None

    @classmethod
    def from_amount(cls, amount: object) -> "KrwAmountDto":
        amount_float = parse_float(amount)
        amount_krw = None if amount_float is None else round(amount_float)
        return cls(krw=amount_krw, human=format_human_krw(amount_krw))
