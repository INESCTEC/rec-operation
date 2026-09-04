from rec_op_lem_prices.custom_types.individual_cost_types import OutputsIndCostDict
from rec_op_lem_prices.custom_types.stage_one_milp_types import OutputsS1Dict
from rec_op_lem_prices.custom_types.stage_two_milp_pool_types import SinglePostOutputsS2PoolDict, OutputsS2PoolDict
from rec_op_lem_prices.custom_types.meters_types import (
	SinglePostMeters,
	SinglePreMeters,
	Meters
)
from typing import (
	TypeAlias,
	TypedDict
)


# -- INPUTS ------------------------------------------------------------------------------------------------------------
class BaseBackpackS3PoolDict(TypedDict):
	delta_t: float
	horizon: int
	l_extra: float
	l_grid: list[float]
	l_market_buy: list[float]
	l_market_sell: list[float]
	strict_pos_coeffs: bool
	total_share_coeffs: bool


class LoopPreBackpackS3PoolDict(BaseBackpackS3PoolDict):
	meters: SinglePreMeters


DualPreBackpackS3PoolDict: TypeAlias = LoopPreBackpackS3PoolDict


class SinglePreBackpackS3PoolDict(LoopPreBackpackS3PoolDict):
	l_lem: list[float]


CollectivePreBackpackS3PoolDict: TypeAlias = SinglePreBackpackS3PoolDict


class LoopPostBackpackS3PoolDict(BaseBackpackS3PoolDict):
	meters: SinglePostMeters


DualPostBackpackS3PoolDict: TypeAlias = LoopPostBackpackS3PoolDict


class SinglePostBackpackS3PoolDict(LoopPostBackpackS3PoolDict):
	l_lem: list[float]


CollectivePostBackpackS3PoolDict: TypeAlias = SinglePostBackpackS3PoolDict


class BackpackS3PoolDict(BaseBackpackS3PoolDict):
	l_lem: list[float]
	meters: Meters
	third_stage: bool


# -- OUTPUTS -----------------------------------------------------------------------------------------------------------
ValuePerId: TypeAlias = dict[
	str, float
]

ListPerId: TypeAlias = dict[
	str, list[float]
]

ListPerIdPerId: TypeAlias = dict[
	str, ListPerId
]


class SinglePostOutputsS3PoolDict(TypedDict):
	c_ind3pool: ValuePerId
	c_ind3pool_without_p_extra: ValuePerId
	delta_alc: ListPerId
	delta_cmet: ListPerId
	delta_coeff: ListPerId
	delta_slc: ListPerId
	delta_sup: ListPerId
	dual_prices: list[float]
	e_alc: ListPerId
	e_cmet: ListPerId
	e_consumed: ListPerId
	e_pur_pool: ListPerId
	e_sale_pool: ListPerId
	e_slc_pool: ListPerId
	e_sup_market: ListPerId
	e_sup_retail: ListPerId
	e_sur_market: ListPerId
	e_sur_retail: ListPerId
	e_flex: ListPerId
	e_gg: ListPerId
	e_curt: ListPerId
	milp_status: str
	obj_value: float
	p_extra: ListPerId
	p_extra_cost3pool: ValuePerId


CollectivePostOutputsS3PoolDict = tuple[
	SinglePostOutputsS3PoolDict,
	SinglePostOutputsS2PoolDict,
	list[OutputsIndCostDict]
]


class OutputsS3PoolDict(SinglePostOutputsS3PoolDict):
	c_ind3pool_without_deg: ValuePerId
	c_ind3pool_without_deg_and_p_extra: ValuePerId
	deg_cost3pool: ValuePerId
	delta_bc: ListPerIdPerId
	e_bat: ListPerIdPerId
	e_bc: ListPerIdPerId
	e_bd: ListPerIdPerId
	soc_bat: ListPerIdPerId


SinglePreOutputsS3PoolDict: TypeAlias = OutputsS3PoolDict

CollectivePreOutputsS3PoolDict = tuple[
	OutputsS3PoolDict,
	OutputsS2PoolDict,
	list[OutputsS1Dict]
]
