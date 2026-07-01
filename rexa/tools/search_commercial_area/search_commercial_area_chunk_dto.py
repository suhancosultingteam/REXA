from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SearchCommercialAreaChunkDto(BaseModel):
    model_config = ConfigDict(extra="allow")

    chunk_uuid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("chunk_uuid", "chunkUuid"),
    )
    score: float | None = None
    text: str | None = None
    matched_query: str | None = None
