import inspect
import numpy as np

import rec_op_lem_prices.pricing_mechanisms.structures.examples as eg

from rec_op_lem_prices.pricing_mechanisms_functions import (
	accepted_offers,
	dual_post_pool,
	dual_pre_pool,
	vanilla_crossing_value,
	vanilla_mmr,
	vanilla_sdr,
	vanilla_mmr_plus,
	vanilla_sdr_plus,
	vanilla_crossing_value_plus,
	loop_post_bilateral_crossing_value,
	loop_post_bilateral_mmr,
	loop_post_bilateral_sdr,
	loop_post_pool_crossing_value,
	loop_post_pool_mmr,
	loop_post_pool_sdr,
	loop_pre_bilateral_crossing_value,
	loop_pre_bilateral_mmr,
	loop_pre_bilateral_sdr,
	loop_pre_pool_crossing_value,
	loop_pre_pool_mmr,
	loop_pre_pool_sdr
)
from rec_op_lem_prices.optimization.structures.I_O_stage_2_pool_milp import (
	DUAL_POST_PRICES_INPUTS,
	DUAL_POST_PRICES_OUTPUTS,
	DUAL_PRE_PRICES_INPUTS,
	DUAL_PRE_PRICES_OUTPUTS,
	LOOP_POST_INPUTS_S2_POOL,
	LOOP_POST_OUTPUTS_S2_POOL_MMR,
	LOOP_POST_OUTPUTS_S2_POOL_SDR,
	LOOP_POST_OUTPUTS_S2_POOL_CV,
	LOOP_PRE_INPUTS_S2_POOL,
	LOOP_PRE_OUTPUTS_S2_POOL_MMR,
	LOOP_PRE_OUTPUTS_S2_POOL_SDR,
	LOOP_PRE_OUTPUTS_S2_POOL_CV
)
from rec_op_lem_prices.optimization.structures.I_O_stage_2_bilateral_milp import (
	LOOP_POST_INPUTS_S2_BILATERAL,
	LOOP_POST_OUTPUTS_S2_BILATERAL_MMR,
	LOOP_POST_OUTPUTS_S2_BILATERAL_SDR,
	LOOP_POST_OUTPUTS_S2_BILATERAL_CV,
	LOOP_PRE_INPUTS_S2_BILATERAL,
	LOOP_PRE_OUTPUTS_S2_BILATERAL_MMR,
	LOOP_PRE_OUTPUTS_S2_BILATERAL_SDR,
	LOOP_PRE_OUTPUTS_S2_BILATERAL_CV
)


def test_accepted_offers():
	expected_lengths = {
		'Example01': (3, 3),
		'Example01a': (3, 3),
		'Example01b': (3, 3),
		'Example02': (3, 3),
		'Example02a': (3, 3),
		'Example02b': (3, 3),
		'Example03': (2, 3),
		'Example04': (2, 3),
		'Example05': (2, 2),
		'Example06': (2, 2),
		'Example07': (3, 2),
		'Example08': (3, 2)
	}

	_classes = inspect.getmembers(eg, inspect.isclass)
	examples = [example_class for _, example_class in _classes]
	for example in examples:
		buy_offers_ = example.buy_offers
		sell_offers_ = example.sell_offers

		accepted_buys, accepted_sells = accepted_offers(buy_offers_, sell_offers_)
		nr_buys = len(accepted_buys)
		nr_sells = len(accepted_sells)
		# assert that the right values are computed
		assert (nr_buys, nr_sells) == expected_lengths.get(example.__name__)


def test_vanilla_mmr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -600, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 50}]

	assert vanilla_mmr(buy_offers, sell_offers, pruned=False) == 10.0
	assert vanilla_mmr(buy_offers, sell_offers) == 22.5
	assert vanilla_mmr(buy_offers, sell_offers, divider=0.25) == 16.25


def test_vanilla_sdr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -400, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 15}]

	assert vanilla_sdr(buy_offers, [], pruned=False) == 45.0
	assert round(vanilla_sdr(buy_offers, sell_offers, compensation=0.5), 3) == 25.485


def test_vanilla_crossing_value():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 1000, 'value': 35},
	              {'origin': 3, 'amount': 1000, 'value': 25},
	              {'origin': 4, 'amount': 500, 'value': 15}]
	sell_offers = [{'origin': 5, 'amount': -1000, 'value': 0},
	               {'origin': 6, 'amount': -1000, 'value': 10},
	               {'origin': 7, 'amount': -1000, 'value': 20}]

	assert vanilla_crossing_value(buy_offers, sell_offers, small_increment=0.0) == 20.0


def test_dual_pre_pool():
	prices, _ = dual_pre_pool(DUAL_PRE_PRICES_INPUTS)
	assert prices == DUAL_PRE_PRICES_OUTPUTS


def test_dual_post_pool():
	prices, _ = dual_post_pool(DUAL_POST_PRICES_INPUTS)
	assert prices == DUAL_POST_PRICES_OUTPUTS


def test_loop_pre_pool_mmr():
	r = loop_pre_pool_mmr(LOOP_PRE_INPUTS_S2_POOL, for_testing=True)
	assert r[:-1] == LOOP_PRE_OUTPUTS_S2_POOL_MMR


def test_loop_post_pool_mmr():
	r = loop_post_pool_mmr(LOOP_POST_INPUTS_S2_POOL, for_testing=True)
	assert r[0] == LOOP_POST_OUTPUTS_S2_POOL_MMR


def test_loop_pre_pool_sdr():
	r = loop_pre_pool_sdr(LOOP_PRE_INPUTS_S2_POOL, for_testing=True)
	assert r[:-1] == LOOP_PRE_OUTPUTS_S2_POOL_SDR


def test_loop_post_pool_sdr():
	r = loop_post_pool_sdr(LOOP_POST_INPUTS_S2_POOL, for_testing=True)
	assert r[0] == LOOP_POST_OUTPUTS_S2_POOL_SDR


def test_loop_pre_pool_crossing_value():
	r = loop_pre_pool_crossing_value(LOOP_PRE_INPUTS_S2_POOL, for_testing=True)
	assert r[:-1] == LOOP_PRE_OUTPUTS_S2_POOL_CV


def test_loop_post_pool_crossing_value():
	r = loop_post_pool_crossing_value(LOOP_POST_INPUTS_S2_POOL, for_testing=True)
	assert r[0] == LOOP_POST_OUTPUTS_S2_POOL_CV


def test_loop_pre_bilateral_mmr():
	r = loop_pre_bilateral_mmr(LOOP_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	assert np.isclose(r[:-1][0], LOOP_PRE_OUTPUTS_S2_BILATERAL_MMR[0]).all()
	assert r[:-1][1:] == LOOP_PRE_OUTPUTS_S2_BILATERAL_MMR[1:]


def test_loop_post_bilateral_mmr():
	r = loop_post_bilateral_mmr(LOOP_POST_INPUTS_S2_BILATERAL, for_testing=True)
	assert r[0] == LOOP_POST_OUTPUTS_S2_BILATERAL_MMR


def test_loop_pre_bilateral_sdr():
	r = loop_pre_bilateral_sdr(LOOP_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	assert r[:-1] == LOOP_PRE_OUTPUTS_S2_BILATERAL_SDR


def test_loop_post_bilateral_sdr():
	r = loop_post_bilateral_sdr(LOOP_POST_INPUTS_S2_BILATERAL, for_testing=True)
	assert r[0] == LOOP_POST_OUTPUTS_S2_BILATERAL_SDR


def test_loop_pre_bilateral_crossing_value():
	r = loop_pre_bilateral_crossing_value(LOOP_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	assert r[:-1] == LOOP_PRE_OUTPUTS_S2_BILATERAL_CV


def test_loop_post_bilateral_crossing_value():
	r = loop_post_bilateral_crossing_value(LOOP_POST_INPUTS_S2_BILATERAL, for_testing=True)
	assert r[0] == LOOP_POST_OUTPUTS_S2_BILATERAL_CV


def test_vanilla_mmr_plus():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
				  {'origin': 2, 'amount': 500, 'value': 40}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
				   {'origin': 5, 'amount': -500, 'value': 10},
				   {'origin': 6, 'amount': -100, 'value': 20}]

	cross_l_p2p, accepted_buy_offers, accepted_sell_offers = vanilla_mmr_plus(buy_offers, sell_offers)
	assert cross_l_p2p == 25.0
	assert accepted_buy_offers == [{'origin': 1, 'amount': 500, 'value': 45},
								   {'origin': 2, 'amount': 500, 'value': 40}]
	assert accepted_sell_offers == [{'origin': 4, 'amount': 500, 'value': 0},
									{'origin': 5, 'amount': 500, 'value': 10}]


def test_vanilla_sdr_plus():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
				  {'origin': 2, 'amount': 500, 'value': 40},
				  {'origin': 3, 'amount': 100, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
				   {'origin': 5, 'amount': -500, 'value': 10}]

	cross_l_p2p, accepted_buy_offers, accepted_sell_offers = vanilla_sdr_plus(buy_offers, sell_offers)
	assert cross_l_p2p == 10.0
	assert accepted_buy_offers == [{'origin': 1, 'amount': 500, 'value': 45},
								   {'origin': 2, 'amount': 500, 'value': 40}]
	assert accepted_sell_offers == [{'origin': 4, 'amount': 500, 'value': 0},
									{'origin': 5, 'amount': 500, 'value': 10}]


def test_vanilla_crossing_value_plus():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
				  {'origin': 2, 'amount': 500, 'value': 40},
				  {'origin': 3, 'amount': 100, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
				   {'origin': 5, 'amount': -500, 'value': 10}]

	cross_l_p2p, accepted_buy_offers, accepted_sell_offers = vanilla_crossing_value_plus(buy_offers, sell_offers)
	assert cross_l_p2p == 35.0
	assert accepted_buy_offers == [{'origin': 1, 'amount': 500, 'value': 45},
								   {'origin': 2, 'amount': 500, 'value': 40}]
	assert accepted_sell_offers == [{'origin': 4, 'amount': 500, 'value': 0},
									{'origin': 5, 'amount': 500, 'value': 10}]


if __name__ == '__main__':
	test_vanilla_mmr()
	test_vanilla_sdr()
	test_vanilla_crossing_value()
	test_dual_pre_pool()
	test_dual_post_pool()
	test_loop_pre_pool_mmr()
	test_loop_post_pool_mmr()
	test_loop_pre_pool_sdr()
	test_loop_post_pool_sdr()
	test_loop_pre_pool_crossing_value()
	test_loop_post_pool_crossing_value()
	test_loop_pre_bilateral_mmr()
	test_loop_post_bilateral_mmr()
	test_loop_pre_bilateral_sdr()
	test_loop_post_bilateral_sdr()
	test_loop_pre_bilateral_crossing_value()
	test_loop_post_bilateral_crossing_value()
	test_vanilla_mmr_plus()
	test_vanilla_sdr_plus()
	test_vanilla_crossing_value_plus()
