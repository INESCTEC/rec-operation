import pandas as pd

from datetime import datetime, timedelta
from rec_op_lem_prices.configs.configs import DT_FORMAT
from rec_op_lem_prices.custom_types.optimization_helpers_types import (
	ForecastsList,
	InputDatadict
)


def iter_dt(first: datetime, last: datetime, delta: timedelta):
	"""
	Creates an iterator ranging from first datetime to last datetime (inclusive)
	with a delta step
	:param first: first datetime
	:param last: last datetime
	:param delta: timedelta step
	:return:
	"""
	curr = first
	while curr <= last:
		yield curr
		curr += delta


def remove_out_of_range(forecasts: ForecastsList, start: datetime, end: datetime,
                        dt_key='datetime') -> ForecastsList:
	"""
	Returns a pruned version of input forecasts list without dicts
	with "datetime" outside the request range
	:param forecasts: raw list of dictionaries with forecast data
	:param start: start datetime
	:param end: end datetime
	:param dt_key: dictionary key of datetime value
	:return: pruned forecasts' list
	"""
	if forecasts is not None:
		check_list = forecasts.copy()
		for f in check_list:
			dt = f[dt_key]
			if (end < dt) or (start > dt):
				forecasts.remove(f)
	return forecasts


def substitute_by_measure(forecasts_list: ForecastsList, unique_id: str, input_data: InputDatadict,
                          substruct_key: str, measure_key: str):
	"""
	For substituting the first element in forecast_list by the respective measure,
	given the unique_id (which can be a peer_id or upac_id)
	:param forecasts_list: list of forecast data (floats)
	:param unique_id: id that identifies a given peer or upac
	:param input_data: dictionary where the measured data points can be found under 'substruct_key'
	:param substruct_key: either 'peer_measures' or 'upac_measures'
	:param measure_key: within input_data[substruct_key] is a list of dictionaries where the
	measure can be found under this key
	:return:
	"""
	id_key = 'peer_id' if substruct_key == 'peer_measures' else 'upac_id'
	if input_data.get(substruct_key) is not None:
		measures = [m for m in input_data.get(substruct_key) if m.get(id_key) == unique_id]
		if measures:
			measure = measures[0].get(measure_key)
			if measure:
				forecasts_list[0] = measure

	return
