from rec_op_lem_prices.optimization.module.IndividualCost import calculate_individual_cost
from rec_op_lem_prices.optimization.structures.I_O_individual_cost import (
		INPUTS_IC,
		OUTPUTS_IC
	)


def test_solve_individual_milp():
	# Assert the correct ouputs
	results = calculate_individual_cost(INPUTS_IC)
	results['c_ind'] = round(results['c_ind'], 3)
	results['p_extra'] = [round(p, 3) for p in results['p_extra']]
	for ki, valu in results.items():
		assert valu == OUTPUTS_IC.get(ki), f'{ki}'
