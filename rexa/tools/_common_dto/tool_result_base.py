from pydantic import BaseModel


class ToolResultBase(BaseModel):
    def __str__(self) -> str:
        return self.model_dump_json(exclude_none=True)
