from rec_op_lem_prices.optimization.module.StageOneMILP import StageOneMILP
from rec_op_lem_prices.optimization.structures.I_O_stage_1_milp_ewh import (
	INPUTS_S1_EWH,
	OUTPUTS_S1_EWH
)

from rec_op_lem_prices.optimization.module.StageTwoMILPPool import StageTwoMILPPool
from rec_op_lem_prices.optimization.structures.I_O_stage_2_pool_milp_ewh import (
	INPUTS_S2_DUAL_EWH,
	INPUTS_S2_POOL_EWH,
	OUTPUTS_S2_DUAL_EWH,
	OUTPUTS_S2_POOL_EWH
)

from rec_op_lem_prices.optimization.module.StageTwoMILPBilateral import StageTwoMILPBilateral
from rec_op_lem_prices.optimization.structures.I_O_stage_2_bilateral_milp_ewh import (
	INPUTS_S2_BILATERAL_EWH,
	OUTPUTS_S2_BILATERAL_EWH
)


# Test Stage One
def test_solve_individual_milp():
	# Assert the creation of a correct class
	milp = StageOneMILP(INPUTS_S1_EWH)
	assert isinstance(milp, StageOneMILP)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Assert the correct ouputs
	results = milp.generate_outputs()
	results['deg_cost'] = round(results['deg_cost'], 3)
	for ki, valu in results.items():
		assert valu == OUTPUTS_S1_EWH.get(ki), f'{ki}'


# Test Stage Two Pool
def test_solve_collective_pool_milp():
	# Assert the creation of a correct class
	milp = StageTwoMILPPool(INPUTS_S2_POOL_EWH)
	assert isinstance(milp, StageTwoMILPPool)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Assert the correct ouputs
	results = milp.generate_outputs()
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	results['c_ind2pool'] = round_cost(results['c_ind2pool'])
	results['c_ind2pool_without_deg'] = round_cost(results['c_ind2pool_without_deg'])
	results['c_ind2pool_without_deg_and_p_extra'] = round_cost(results['c_ind2pool_without_deg_and_p_extra'])
	results['c_ind2pool_without_p_extra'] = round_cost(results['c_ind2pool_without_p_extra'])
	results['dual_prices'] = [round(dp, 3) for dp in results['dual_prices']]
	for ki, valu in results.items():
		assert valu == OUTPUTS_S2_POOL_EWH.get(ki), f'{ki}'


def test_solve_collective_dual_milp():
	# Assert the creation of a correct class
	milp = StageTwoMILPPool(INPUTS_S2_DUAL_EWH)
	assert isinstance(milp, StageTwoMILPPool)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Assert the correct ouputs
	results = milp.generate_outputs()
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	results['c_ind2pool'] = round_cost(results['c_ind2pool'])
	results['c_ind2pool_without_deg'] = round_cost(results['c_ind2pool_without_deg'])
	results['c_ind2pool_without_deg_and_p_extra'] = round_cost(results['c_ind2pool_without_deg_and_p_extra'])
	results['c_ind2pool_without_p_extra'] = round_cost(results['c_ind2pool_without_p_extra'])
	results['obj_value'] = round(results['obj_value'], 3)
	for ki, valu in results.items():
		assert valu == OUTPUTS_S2_DUAL_EWH.get(ki), f'{ki}'


# Test Stage Two Bilateral
def test_solve_collective_bilateral_milp():
	# Assert the creation of a correct class
	milp = StageTwoMILPBilateral(INPUTS_S2_BILATERAL_EWH)
	assert isinstance(milp, StageTwoMILPBilateral)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Assert the correct ouputs
	results = milp.generate_outputs()
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	results['obj_value'] = round(results['obj_value'], 3)
	results['c_ind2bilateral'] = round_cost(results['c_ind2bilateral'])
	results['c_ind2bilateral_without_deg'] = round_cost(results['c_ind2bilateral_without_deg'])
	results['c_ind2bilateral_without_deg_and_p_extra'] = round_cost(results['c_ind2bilateral_without_deg_and_p_extra'])
	results['c_ind2bilateral_without_p_extra'] = round_cost(results['c_ind2bilateral_without_p_extra'])
	for ki, valu in results.items():
		assert valu == OUTPUTS_S2_BILATERAL_EWH.get(ki), f'{ki}'


if __name__ == '__main__':
	# test_solve_individual_milp()
	# test_solve_collective_bilateral_milp()
	# test_solve_collective_pool_milp()
	test_solve_collective_dual_milp()
