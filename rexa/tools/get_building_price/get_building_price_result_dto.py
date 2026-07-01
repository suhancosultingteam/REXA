from rexa.tools._common_dto.krw_amount_dto import KrwAmountDto
from rexa.tools._common_dto.tool_result_base import ToolResultBase
from rexa.tools.get_building_price.get_building_price_adjustment_dto import GetBuildingPriceAdjustmentDto
from rexa.tools.get_building_price.get_building_price_comparable_dto import GetBuildingPriceComparableDto
from rexa.tools.get_building_price.get_building_price_stage_dto import GetBuildingPriceStageDto
from rexa.tools.get_building_price.get_building_price_target_dto import GetBuildingPriceTargetDto


class GetBuildingPriceResultDto(ToolResultBase):
    error: str | None = None
    detail: str | None = None
    building: GetBuildingPriceTargetDto | None = None      # error 시 동봉
    land_context: dict | None = None                       # error 시 동봉
    candidate_universe_count: int | None = None
    reference_land_price_year: int | None = None
    stage_attempts: list[dict] | None = None
    calculation_logs: list[str] | None = None

    # 정상 결과
    target_building: GetBuildingPriceTargetDto | None = None
    selected_stage: GetBuildingPriceStageDto | None = None
    comparable_count: int | None = None
    base_estimated_price: KrwAmountDto | None = None
    final_estimated_price: KrwAmountDto | None = None
    adjustments: list[GetBuildingPriceAdjustmentDto] | None = None
    selected_comparables: list[GetBuildingPriceComparableDto] | None = None

    # excluded 케이스
    excluded: bool | None = None
    message: str | None = None
