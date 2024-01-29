from rec_op_lem_prices.optimization.module.StageTwoMILPBilateral import StageTwoMILPBilateral
from rec_op_lem_prices.optimization.structures.I_O_stage_2_bilateral_milp import (
	INPUTS_S2_BILATERAL,
	OUTPUTS_S2_BILATERAL
)


def test_solve_collective_bilateral_milp():
	# Assert the creation of a correct class
	milp = StageTwoMILPBilateral(INPUTS_S2_BILATERAL)
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
		assert valu == OUTPUTS_S2_BILATERAL.get(ki), f'{ki}'
