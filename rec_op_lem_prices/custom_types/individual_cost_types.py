from typing import TypedDict


# -- INPUTS ------------------------------------------------------------------------------------------------------------
class BackpackIndCostDict(TypedDict):
	delta_t: float
	e_met: list[float]
	id: str
	l_buy: list[float]
	l_extra: float
	l_market_buy: list[float]
	l_market_sell: list[float]
	l_sell: list[float]
	max_p: float


# -- OUTPUTS -----------------------------------------------------------------------------------------------------------
class OutputsIndCostDict(TypedDict):
	c_ind: float
	meter_id: str
	e_sup_market: list[float]
	e_sup_retail: list[float]
	e_sur_market: list[float]
	e_sur_retail: list[float]
	p_extra: list[float]
