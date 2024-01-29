from rec_op_lem_prices.custom_types.btm_storage_types import BtmStorage
from typing import (
	TypeAlias,
	TypedDict,
	Union
)


class SinglePostMeter(TypedDict):
	e_c: list[float]
	e_g: list[float]
	l_buy: list[float]
	l_sell: list[float]
	max_p: float


class SinglePreMeter(SinglePostMeter):
	btm_storage: Union[BtmStorage, None]


class SingleMeter(SinglePreMeter):
	c_ind: float


SinglePostMeters: TypeAlias = dict[
	str, SinglePostMeter
]

SinglePreMeters: TypeAlias = dict[
	str, SinglePreMeter
]

Meters: TypeAlias = dict[
	str, SingleMeter
]
