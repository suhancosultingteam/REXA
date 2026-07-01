from typing import Literal

from pydantic import BaseModel


class GetBuildingPriceAdjustmentDto(BaseModel):
    type: Literal["station_access", "road_contact", "building_age", "terrain_shape"] | None = None
    rate: float | None = None
    reason: str | None = None
