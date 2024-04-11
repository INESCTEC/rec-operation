from rec_op_lem_prices.optimization_functions import (
	run_pre_individual_milp,
	run_pre_single_stage_collective_pool_milp,
	run_pre_single_stage_collective_bilateral_milp,
	run_pre_two_stage_collective_pool_milp,
	run_pre_two_stage_collective_bilateral_milp,
	run_post_individual_cost,
	run_post_single_stage_collective_pool_milp,
	run_post_single_stage_collective_bilateral_milp,
	run_post_two_stage_collective_pool_milp,
	run_post_two_stage_collective_bilateral_milp
)
from rec_op_lem_prices.optimization.structures.I_O_individual_cost import (
	INPUTS_IC,
	OUTPUTS_IC
)
from rec_op_lem_prices.optimization.structures.I_O_stage_1_milp import (
	INPUTS_S1,
	OUTPUTS_S1
)
from rec_op_lem_prices.optimization.structures.I_O_stage_2_bilateral_milp import (
	COLLECTIVE_POST_INPUTS_S2_BILATERAL,
	COLLECTIVE_POST_OUTPUTS_S2_BILATERAL,
	COLLECTIVE_PRE_INPUTS_S2_BILATERAL,
	COLLECTIVE_PRE_OUTPUTS_S2_BILATERAL,
	SINGLE_POST_INPUTS_S2_BILATERAL,
	SINGLE_POST_OUTPUTS_S2_BILATERAL,
	SINGLE_PRE_INPUTS_S2_BILATERAL,
	SINGLE_PRE_OUTPUTS_S2_BILATERAL
)
from rec_op_lem_prices.optimization.structures.I_O_stage_2_pool_milp import (
	COLLECTIVE_POST_INPUTS_S2_POOL,
	COLLECTIVE_POST_OUTPUTS_S2_POOL,
	COLLECTIVE_PRE_INPUTS_S2_POOL,
	COLLECTIVE_PRE_OUTPUTS_S2_POOL,
	SINGLE_POST_INPUTS_S2_POOL,
	SINGLE_POST_OUTPUTS_S2_POOL,
	SINGLE_PRE_INPUTS_S2_POOL,
	SINGLE_PRE_OUTPUTS_S2_POOL
)


def test_run_pre_individual_milp():
	r = run_pre_individual_milp(INPUTS_S1)
	r['deg_cost'] = round(r['deg_cost'], 3)
	for ki, valu in r.items():
		assert valu == OUTPUTS_S1.get(ki), f'{ki}'


def test_run_pre_single_stage_collective_pool_milp():
	r = run_pre_single_stage_collective_pool_milp(SINGLE_PRE_INPUTS_S2_POOL)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r['c_ind2pool'] = round_cost(r['c_ind2pool'])
	r['c_ind2pool_without_deg'] = round_cost(r['c_ind2pool_without_deg'])
	r['c_ind2pool_without_deg_and_p_extra'] = round_cost(r['c_ind2pool_without_deg_and_p_extra'])
	r['c_ind2pool_without_p_extra'] = round_cost(r['c_ind2pool_without_p_extra'])
	for ki, valu in r.items():
		assert valu == SINGLE_PRE_OUTPUTS_S2_POOL.get(ki), f'{ki}'


def test_run_pre_single_stage_collective_bilateral_milp():
	r = run_pre_single_stage_collective_bilateral_milp(SINGLE_PRE_INPUTS_S2_BILATERAL)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r['obj_value'] = round(r['obj_value'], 3)
	r['c_ind2bilateral'] = round_cost(r['c_ind2bilateral'])
	r['c_ind2bilateral_without_deg'] = round_cost(r['c_ind2bilateral_without_deg'])
	r['c_ind2bilateral_without_deg_and_p_extra'] = round_cost(r['c_ind2bilateral_without_deg_and_p_extra'])
	r['c_ind2bilateral_without_p_extra'] = round_cost(r['c_ind2bilateral_without_p_extra'])
	for ki, valu in r.items():
		assert valu == SINGLE_PRE_OUTPUTS_S2_BILATERAL.get(ki), f'{ki}'


def test_run_pre_two_stage_collective_pool_milp():
	r2, r1_list = run_pre_two_stage_collective_pool_milp(COLLECTIVE_PRE_INPUTS_S2_POOL, for_testing=True)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r2['c_ind2pool'] = round_cost(r2['c_ind2pool'])
	r2['c_ind2pool_without_deg'] = round_cost(r2['c_ind2pool_without_deg'])
	r2['c_ind2pool_without_deg_and_p_extra'] = round_cost(r2['c_ind2pool_without_deg_and_p_extra'])
	r2['c_ind2pool_without_p_extra'] = round_cost(r2['c_ind2pool_without_p_extra'])
	for ki, valu in r2.items():
		assert valu == COLLECTIVE_PRE_OUTPUTS_S2_POOL[0].get(ki), f'{ki}'
	for idx, r1 in enumerate(r1_list):
		for ki, valu in r1.items():
			assert valu == COLLECTIVE_PRE_OUTPUTS_S2_POOL[1][idx].get(ki), f'{ki}'


def test_run_pre_two_stage_collective_bilateral_milp():
	r2, r1_list = run_pre_two_stage_collective_bilateral_milp(COLLECTIVE_PRE_INPUTS_S2_BILATERAL, for_testing=True)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r2['obj_value'] = round(r2['obj_value'], 3)
	r2['c_ind2bilateral'] = round_cost(r2['c_ind2bilateral'])
	r2['c_ind2bilateral_without_deg'] = round_cost(r2['c_ind2bilateral_without_deg'])
	r2['c_ind2bilateral_without_deg_and_p_extra'] = round_cost(r2['c_ind2bilateral_without_deg_and_p_extra'])
	r2['c_ind2bilateral_without_p_extra'] = round_cost(r2['c_ind2bilateral_without_p_extra'])
	for ki, valu in r2.items():
		assert valu == COLLECTIVE_PRE_OUTPUTS_S2_BILATERAL[0].get(ki), f'{ki}'
	for idx, r1 in enumerate(r1_list):
		r1['c_ind'] = round(r1['c_ind'], 3)
		r1['c_ind_without_deg'] = round(r1['c_ind_without_deg'], 3)
		r1['c_ind_without_p_extra'] = round(r1['c_ind_without_p_extra'], 3)
		r1['c_ind_without_deg_and_p_extra'] = round(r1['c_ind_without_deg_and_p_extra'], 3)
		r1['deg_cost'] = round(r1['deg_cost'], 3)
		r1['obj_value'] = round(r1['obj_value'], 3)
		for ki, valu in r1.items():
			assert valu == COLLECTIVE_PRE_OUTPUTS_S2_BILATERAL[1][idx].get(ki), f'{ki}'


def test_run_post_individual_cost():
	r = run_post_individual_cost(INPUTS_IC)
	r['c_ind'] = round(r['c_ind'], 3)
	r['p_extra'] = [round(p, 3) for p in r['p_extra']]
	for ki, valu in r.items():
		assert valu == OUTPUTS_IC.get(ki), f'{ki}'


def test_run_post_single_stage_collective_pool_milp():
	r = run_post_single_stage_collective_pool_milp(SINGLE_POST_INPUTS_S2_POOL)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r['obj_value'] = round(r['obj_value'], 3)
	r['c_ind2pool'] = round_cost(r['c_ind2pool'])
	r['c_ind2pool_without_p_extra'] = round_cost(r['c_ind2pool_without_p_extra'])
	for ki, valu in r.items():
		assert valu == SINGLE_POST_OUTPUTS_S2_POOL.get(ki), f'{ki}'


def test_run_post_single_stage_collective_bilateral_milp():
	r = run_post_single_stage_collective_bilateral_milp(SINGLE_POST_INPUTS_S2_BILATERAL)
	for ki, valu in r.items():
		assert valu == SINGLE_POST_OUTPUTS_S2_BILATERAL.get(ki), f'{ki}'


def test_run_post_two_stage_collective_pool_milp():
	r2, r1_list = run_post_two_stage_collective_pool_milp(COLLECTIVE_POST_INPUTS_S2_POOL, for_testing=True)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r2['obj_value'] = round(r2['obj_value'], 3)
	r2['c_ind2pool'] = round_cost(r2['c_ind2pool'])
	r2['c_ind2pool_without_p_extra'] = round_cost(r2['c_ind2pool_without_p_extra'])
	for ki, valu in r2.items():
		assert valu == COLLECTIVE_POST_OUTPUTS_S2_POOL[0].get(ki), f'{ki}'
	for idx, r1 in enumerate(r1_list):
		r1['c_ind'] = round(r1['c_ind'], 3)
		for ki, valu in r1.items():
			assert valu == COLLECTIVE_POST_OUTPUTS_S2_POOL[1][idx].get(ki), f'{ki}'


def test_run_post_two_stage_collective_bilateral_milp():
	r2, r1_list = run_post_two_stage_collective_bilateral_milp(COLLECTIVE_POST_INPUTS_S2_BILATERAL, for_testing=True)
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	r2['c_ind2bilateral'] = round_cost(r2['c_ind2bilateral'])
	r2['c_ind2bilateral_without_p_extra'] = round_cost(r2['c_ind2bilateral_without_p_extra'])
	for ki, valu in r2.items():
		assert valu == COLLECTIVE_POST_OUTPUTS_S2_BILATERAL[0].get(ki), f'{ki}'
	for idx, r1 in enumerate(r1_list):
		r1['c_ind'] = round(r1['c_ind'], 3)
		for ki, valu in r1.items():
			assert valu == COLLECTIVE_POST_OUTPUTS_S2_BILATERAL[1][idx].get(ki), f'{ki}'


if __name__ == '__main__':
	test_run_pre_individual_milp()
	test_run_pre_single_stage_collective_pool_milp()
	test_run_pre_single_stage_collective_bilateral_milp()
	test_run_pre_two_stage_collective_pool_milp()
	test_run_pre_two_stage_collective_bilateral_milp()
	test_run_post_individual_cost()
	test_run_post_single_stage_collective_pool_milp()
	test_run_post_single_stage_collective_bilateral_milp()
	test_run_post_two_stage_collective_pool_milp()
	test_run_post_two_stage_collective_bilateral_milp()
