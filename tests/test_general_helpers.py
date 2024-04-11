from datetime import datetime, timedelta, timezone
from rec_op_lem_prices.optimization.helpers.general_helpers import (
	iter_dt,
	remove_out_of_range,
	substitute_by_measure
)


def test_iter_dt():
	start = datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone.utc)
	end = datetime(year=2023, month=1, day=2, hour=0, minute=0, second=0, tzinfo=timezone.utc)
	delta = timedelta(hours=1)
	lst = list(iter_dt(start, end, delta))
	assert len(lst) == 25  # assert the length of the generator
	assert lst[0] == start  # assert that start is included
	assert lst[-1] == end  # assert that end is also included
	assert lst[1] - lst[0] == timedelta(hours=1)  # assert the timedelta between elements


def test_remove_out_of_range():
	keep = datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone.utc)
	discard = datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone.utc)
	lst = [
		{'datetime': keep},
		{'datetime': discard}
	]
	# assert that the right element is kept and the other discarded
	assert remove_out_of_range(lst, keep, keep + timedelta(hours=1)) == [{'datetime': keep}]


def test_substitute_by_measure():
	peer_data = {'peer_measures': [{'peer_id': 'A', 'measure': 5}, {'peer_id': 'B', 'measure': 6}]}
	upac_data = {'upac_measures': [{'upac_id': 'A', 'measure': 5}, {'upac_id': 'B', 'measure': 6}]}
	peer_forecasts = [10, 10]
	upac_forecasts = [10, 10]
	substitute_by_measure(peer_forecasts, 'A', peer_data, 'peer_measures', 'measure')
	substitute_by_measure(upac_forecasts, 'A', upac_data, 'upac_measures', 'measure')
	# assert that the first element of id 'A' is substituted by 'measure'
	assert peer_forecasts == [5, 10]
	assert upac_forecasts == [5, 10]


if __name__ == '__main__':
	test_iter_dt()
	test_remove_out_of_range()
	test_substitute_by_measure()
