from rec_op_lem_prices.optimization.module.StageOneMILP import StageOneMILP
from rec_op_lem_prices.optimization.structures.I_O_stage_1_milp import (
	INPUTS_S1,
	OUTPUTS_S1
)


def test_solve_individual_milp():
	# Assert the creation of a correct class
	milp = StageOneMILP(INPUTS_S1)
	assert isinstance(milp, StageOneMILP)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Assert the correct ouputs
	results = milp.generate_outputs()
	results['deg_cost'] = round(results['deg_cost'], 3)
	for ki, valu in results.items():
		assert valu == OUTPUTS_S1.get(ki), f'{ki}'
