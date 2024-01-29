from typing import TypedDict


class RequestParams(TypedDict):
	pruned: bool  # if True, triggers prunned versions of MMR or SDR
	compensation: float  # compensatin, between 0 and 1 to apply to SDR
	increment: float  # small increment to apply to crossing_value function
	divisor: float  # divisor, >= 0 to apply to MMR
