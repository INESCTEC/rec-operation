from rec_op_lem_prices.custom_types.individual_cost_types import OutputsIndCostDict
from rec_op_lem_prices.custom_types.stage_one_milp_types import OutputsS1Dict
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
class BaseBackpackS2PoolDict(TypedDict):
	delta_t: float
	horizon: int
	l_extra: float
	l_grid: list[float]
	l_market_buy: list[float]
	l_market_sell: list[float]
	strict_pos_coeffs: bool
	sum_one_coeffs: bool


class LoopPreBackpackS2PoolDict(BaseBackpackS2PoolDict):
	meters: SinglePreMeters


DualPreBackpackS2PoolDict: TypeAlias = LoopPreBackpackS2PoolDict


class SinglePreBackpackS2PoolDict(LoopPreBackpackS2PoolDict):
	l_lem: list[float]


CollectivePreBackpackS2PoolDict: TypeAlias = SinglePreBackpackS2PoolDict


class LoopPostBackpackS2PoolDict(BaseBackpackS2PoolDict):
	meters: SinglePostMeters


DualPostBackpackS2PoolDict: TypeAlias = LoopPostBackpackS2PoolDict


class SinglePostBackpackS2PoolDict(LoopPostBackpackS2PoolDict):
	l_lem: list[float]


CollectivePostBackpackS2PoolDict: TypeAlias = SinglePostBackpackS2PoolDict


class BackpackS2PoolDict(BaseBackpackS2PoolDict):
	l_lem: list[float]
	meters: Meters
	second_stage: bool


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


class SinglePostOutputsS2PoolDict(TypedDict):
	c_ind2pool: ValuePerId
	c_ind2pool_without_p_extra: ValuePerId
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
	milp_status: str
	obj_value: float
	p_extra: ListPerId
	p_extra_cost2pool: ValuePerId


CollectivePostOutputsS2PoolDict = tuple[
	SinglePostOutputsS2PoolDict,
	list[OutputsIndCostDict]
]


class OutputsS2PoolDict(SinglePostOutputsS2PoolDict):
	c_ind2pool_without_deg: ValuePerId
	c_ind2pool_without_deg_and_p_extra: ValuePerId
	deg_cost2pool: ValuePerId
	delta_bc: ListPerIdPerId
	e_bat: ListPerIdPerId
	e_bc: ListPerIdPerId
	e_bd: ListPerIdPerId
	soc_bat: ListPerIdPerId


SinglePreOutputsS2PoolDict: TypeAlias = OutputsS2PoolDict

CollectivePreOutputsS2PoolDict = tuple[
	OutputsS2PoolDict,
	list[OutputsS1Dict]
]
