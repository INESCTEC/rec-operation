from typing import (
	TypeAlias,
	TypedDict,
	Union
)


# general_helpers.py
ForecastsList: TypeAlias = list[dict]


class SinglePeerMeasuresDict(TypedDict):
	peer_id: str
	measure: float


class SingleUpacMeasuresDict(TypedDict):
	upac_id: str
	measure: float


class PeerMeasuresDict(TypedDict):
	peer_measures: list[SinglePeerMeasuresDict]


class UpacMeasuresDict(TypedDict):
	upac_measures: list[SingleUpacMeasuresDict]


InputDatadict: TypeAlias = Union[PeerMeasuresDict, UpacMeasuresDict]

# milp_helpers.py
MetersDict: TypeAlias = dict[
	str, dict[
		str, list[float]
	]
]
MetersParamDict: TypeAlias = dict[
	str, list[float]
]
