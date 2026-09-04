from typing import (
	TypeAlias,
	TypedDict
)


class Singlebtmevs(TypedDict):
	trip_ev: list
	min_energy_storage_ev: float
	battery_capacity_ev: float
	eff_bc_ev: float
	eff_bd_ev: float
	init_e_ev: float
	pmax_c_ev: float
	pmax_d_ev: float
	bin_ev: list

Btmevs: TypeAlias = dict[
	str, Singlebtmevs
]
