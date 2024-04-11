from rec_op_lem_prices.custom_types.btm_storage_types import BtmStorage
from typing import (
	TypeAlias,
	TypedDict
)


# -- INPUTS ------------------------------------------------------------------------------------------------------------
class BackpackS1Dict(TypedDict):
	btm_storage: BtmStorage
	delta_t: float
	e_c: list[float]
	e_g: list[float]
	horizon: int
	id: str
	l_buy: list[float]
	l_extra: float
	l_market_buy: list[float]
	l_market_sell: list[float]
	l_sell: list[float]
	max_p: float


# -- OUTPUTS -----------------------------------------------------------------------------------------------------------
BtmStorageOutputsDict: TypeAlias = dict[
	str, list[float]
]


class OutputsS1Dict(TypedDict):
	c_ind: float
	c_ind_without_deg: float
	c_ind_without_deg_and_p_extra: float
	c_ind_without_p_extra: float
	deg_cost: float
	delta_bc: BtmStorageOutputsDict
	delta_sup: list[float]
	e_bat: BtmStorageOutputsDict
	e_bc: BtmStorageOutputsDict
	e_bd: BtmStorageOutputsDict
	e_cmet: list[float]
	e_sup_market: list[float]
	e_sup_retail: list[float]
	e_sur_market: list[float]
	e_sur_retail: list[float]
	meter_id: str
	milp_status: str
	obj_value: float
	p_extra: list[float]
	p_extra_cost: float
	soc_bat: BtmStorageOutputsDict
