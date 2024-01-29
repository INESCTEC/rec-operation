from typing import (
	TypeAlias,
	TypedDict
)


class OfferDict(TypedDict):
	origin: str
	amount: float
	value: float


OffersList: TypeAlias = list[OfferDict]
PricesList: TypeAlias = list[float]
