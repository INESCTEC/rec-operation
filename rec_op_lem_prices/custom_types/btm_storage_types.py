from typing import (
	TypeAlias,
	TypedDict
)


class SingleBtmStorage(TypedDict):
	degradation_cost: float
	e_bn: float
	eff_bc: float
	eff_bd: float
	init_e: float
	p_max: float
	soc_max: float
	soc_min: float


BtmStorage: TypeAlias = dict[
	str, SingleBtmStorage
]
