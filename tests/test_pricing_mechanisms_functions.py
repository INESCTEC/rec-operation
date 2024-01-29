from rec_op_lem_prices.pricing_mechanisms_functions import (
	dual_post_pool,
	dual_pre_pool,
	vanilla_crossing_value,
	vanilla_mmr,
	vanilla_sdr,
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


def test_vanilla_mmr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -600, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 50}]

	assert vanilla_mmr(buy_offers, sell_offers, pruned=False) == 10.0
	assert vanilla_mmr(buy_offers, sell_offers) == 22.5
	assert vanilla_mmr(buy_offers, sell_offers, divisor=4) == 11.25


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
	r = dual_pre_pool(DUAL_PRE_PRICES_INPUTS)
	assert r == DUAL_PRE_PRICES_OUTPUTS


def test_dual_post_pool():
	r = dual_post_pool(DUAL_POST_PRICES_INPUTS)
	assert r == DUAL_POST_PRICES_OUTPUTS


def test_loop_pre_pool_mmr():
	r = loop_pre_pool_mmr(LOOP_PRE_INPUTS_S2_POOL, for_testing=True)
	assert r == LOOP_PRE_OUTPUTS_S2_POOL_MMR


def test_loop_post_pool_mmr():
	r = loop_post_pool_mmr(LOOP_POST_INPUTS_S2_POOL, for_testing=True)
	assert r == LOOP_POST_OUTPUTS_S2_POOL_MMR


def test_loop_pre_pool_sdr():
	r = loop_pre_pool_sdr(LOOP_PRE_INPUTS_S2_POOL, for_testing=True)
	assert r == LOOP_PRE_OUTPUTS_S2_POOL_SDR


def test_loop_post_pool_sdr():
	r = loop_post_pool_sdr(LOOP_POST_INPUTS_S2_POOL, for_testing=True)
	assert r == LOOP_POST_OUTPUTS_S2_POOL_SDR


def test_loop_pre_pool_crossing_value():
	r = loop_pre_pool_crossing_value(LOOP_PRE_INPUTS_S2_POOL, for_testing=True)
	assert r == LOOP_PRE_OUTPUTS_S2_POOL_CV


def test_loop_post_pool_crossing_value():
	r = loop_post_pool_crossing_value(LOOP_POST_INPUTS_S2_POOL, for_testing=True)
	assert r == LOOP_POST_OUTPUTS_S2_POOL_CV


def test_loop_pre_bilateral_mmr():
	r = loop_pre_bilateral_mmr(LOOP_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	assert r == LOOP_PRE_OUTPUTS_S2_BILATERAL_MMR


def test_loop_post_bilateral_mmr():
	r = loop_post_bilateral_mmr(LOOP_POST_INPUTS_S2_BILATERAL, for_testing=True)
	assert r == LOOP_POST_OUTPUTS_S2_BILATERAL_MMR


def test_loop_pre_bilateral_sdr():
	r = loop_pre_bilateral_sdr(LOOP_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	assert r == LOOP_PRE_OUTPUTS_S2_BILATERAL_SDR


def test_loop_post_bilateral_sdr():
	r = loop_post_bilateral_sdr(LOOP_POST_INPUTS_S2_BILATERAL, for_testing=True)
	assert r == LOOP_POST_OUTPUTS_S2_BILATERAL_SDR


def test_loop_pre_bilateral_crossing_value():
	r = loop_pre_bilateral_crossing_value(LOOP_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	assert r == LOOP_PRE_OUTPUTS_S2_BILATERAL_CV


def test_loop_post_bilateral_crossing_value():
	r = loop_post_bilateral_crossing_value(LOOP_POST_INPUTS_S2_BILATERAL, for_testing=True)
	assert r == LOOP_POST_OUTPUTS_S2_BILATERAL_CV
