from rec_op_lem_prices.optimization.module.StageOneMILP import StageOneMILP

from rec_op_lem_prices.optimization.structures.I_O_stage_1_milp_hvac import (
	INPUTS_S1_HVAC,
	OUTPUTS_S1_HVAC
)


def test_solve_individual_milp():
	# Initialize MILP with the input parameters
	milp = StageOneMILP(INPUTS_S1_HVAC)
	assert isinstance(milp, StageOneMILP)

	# Solve the MILP problem
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Generate outputs
	results = milp.generate_outputs()
	results['deg_cost'] = round(results['deg_cost'], 3)
	for ki, valu in results.items():
		assert valu == OUTPUTS_S1_HVAC.get(ki), f'{ki}'

if __name__ == '__main__':
	test_solve_individual_milp()