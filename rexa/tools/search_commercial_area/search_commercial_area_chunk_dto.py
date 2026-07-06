from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SearchCommercialAreaChunkDto(BaseModel):
    model_config = ConfigDict(extra="allow")

    chunk_uuid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("chunk_uuid", "chunkUuid"),
    )
    score: float | None = Field(
        default=None,
        validation_alias=AliasChoices("score", "similarity", "searchScore", "@search.score"),
    )
    text: str | None = Field(
        default=None,
        validation_alias=AliasChoices("text", "chunkText", "chunk_text", "content", "body", "summary"),
    )
    matched_query: str | None = None
