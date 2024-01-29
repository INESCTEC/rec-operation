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
LGridBilateral: TypeAlias = dict[
	str, dict[
		str, list[float]
	]
]


class BaseBackpackS2BilateralDict(TypedDict):
	delta_t: float
	horizon: int
	l_extra: float
	l_grid: LGridBilateral
	l_market_buy: list[float]
	l_market_sell: list[float]
	strict_pos_coeffs: bool
	sum_one_coeffs: bool


class LoopPreBackpackS2BilateralDict(BaseBackpackS2BilateralDict):
	meters: SinglePreMeters


class SinglePreBackpackS2BilateralDict(LoopPreBackpackS2BilateralDict):
	l_lem: list[float]


CollectivePreBackpackS2BilateralDict: TypeAlias = SinglePreBackpackS2BilateralDict


class LoopPostBackpackS2BilateralDict(BaseBackpackS2BilateralDict):
	meters: SinglePostMeters


class SinglePostBackpackS2BilateralDict(LoopPostBackpackS2BilateralDict):
	l_lem: list[float]


CollectivePostBackpackS2BilateralDict: TypeAlias = SinglePostBackpackS2BilateralDict


class BackpackS2BilateralDict(BaseBackpackS2BilateralDict):
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


class SinglePostOutputsS2BilateralDict(TypedDict):
	c_ind2bilateral: ValuePerId
	c_ind2bilateral_without_p_extra: ValuePerId
	delta_alc: ListPerId
	delta_cmet: ListPerId
	delta_coeff: ListPerId
	delta_slc: ListPerId
	delta_sup: ListPerId
	e_alc: ListPerId
	e_cmet: ListPerId
	e_consumed: ListPerId
	e_pur_bilateral: ListPerIdPerId
	e_sale_bilateral: ListPerIdPerId
	e_slc_bilateral: ListPerIdPerId
	e_sup_market: ListPerId
	e_sup_retail: ListPerId
	e_sur_market: ListPerId
	e_sur_retail: ListPerId
	milp_status: str
	obj_value: float
	p_extra: ListPerId
	p_extra_cost2bilateral: ValuePerId


CollectivePostOutputsS2BilateralDict = tuple[
	SinglePostOutputsS2BilateralDict,
	list[OutputsIndCostDict]
]


class OutputsS2BilateralDict(SinglePostOutputsS2BilateralDict):
	c_ind2bilateral_without_deg: ValuePerId
	c_ind2bilateral_without_deg_and_p_extra: ValuePerId
	deg_cost2bilateral: ValuePerId
	delta_bc: ListPerIdPerId
	e_bat: ListPerIdPerId
	e_bc: ListPerIdPerId
	e_bd: ListPerIdPerId
	soc_bat: ListPerIdPerId


SinglePreOutputsS2BilateralDict: TypeAlias = OutputsS2BilateralDict

CollectivePreOutputsS2BilateralDict = tuple[
	OutputsS2BilateralDict,
	list[OutputsS1Dict]
]
