from typing import (
	TypeAlias,
	TypedDict
)


# pricing_helpers.py
EMet: TypeAlias = list[float]
LBuy: TypeAlias = list[float]
LSell: TypeAlias = list[float]


class SingleMeterDict(TypedDict):
	e_met: EMet
	l_buy: LBuy
	l_sell: LSell


MetersDict: TypeAlias = dict[
	str, SingleMeterDict
]
