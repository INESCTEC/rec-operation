import numpy as np

from rec_op_lem_prices.optimization.helpers.milp_helpers import (
	dict_none_lists,
	dict_per_param,
	none_lists,
	round_up,
	time_intervals
)


def test_none_lists():
	list_length = 3
	result = none_lists(list_length)
	# assert the desired length
	assert len(result) == list_length
	# assert that all elements are np.NaN
	assert np.isnan(result).all()


def test_dict_none_lists():
	lists_length = 3
	keys = ['a', 'b', 'c']
	result = dict_none_lists(lists_length, keys)
	# assert the resulting dictionary keys
	assert list(result.keys()) == keys
	# assert the desired length on all lists
	assert all([len(lst) == lists_length for _, lst in result.items()])
	# assert that all elements on all lists are np.NaN
	assert all([np.isnan(lst).all() for _, lst in result.items()])


def test_dict_per_param():
	input_d = {
		'Meter#1': {
			'a': [1, 2, 3],
			'b': [4, 5, 6]
		},
		'Meter#2': {
			'a': [7, 8, 9],
			'b': [10, 11, 12]
		}
	}
	desired_inner_key = 'a'
	desired_output_d = {
		'Meter#1': [1, 2, 3],
		'Meter#2': [7, 8, 9]
	}
	desired_empty_output_d = {
		'Meter#1': None,
		'Meter#2': None
	}
	# assert the correct output if the inner key exists
	assert dict_per_param(input_d, desired_inner_key) == desired_output_d
	# assert the correct output if the inner key does not exist
	assert dict_per_param(input_d, 'mock') == desired_empty_output_d


def test_round_up():
	assert round_up(3.12300000000000001, 3) == 3.124
	assert round_up(3.12550000000000000, 4) == 3.1256


def test_time_intervals():
	# Assert the correct values for a strange delta_t
	assert time_intervals(horizon=2, delta_t=0.75, func='ceil') == 3
	assert time_intervals(horizon=2, delta_t=0.75, func='floor') == 2
	assert time_intervals(horizon=2, delta_t=0.75, func='int') == 2
	# Assert the correct values for a common delta_t
	assert time_intervals(horizon=2, delta_t=0.25, func='ceil') == 8
	assert time_intervals(horizon=2, delta_t=0.25, func='floor') == 8
	assert time_intervals(horizon=2, delta_t=0.25, func='int') == 8
