from rec_op_lem_prices.optimization.module.StageTwoMILPPool import StageTwoMILPPool
from rec_op_lem_prices.optimization.structures.I_O_stage_2_pool_milp_hvac import (
	INPUTS_S2_POOL_HVAC,
	OUTPUTS_S2_POOL_HVAC
)

def test_solve_collective_pool_milp():
	# Assert the creation of a correct class
	milp = StageTwoMILPPool(INPUTS_S2_POOL_HVAC)
	assert isinstance(milp, StageTwoMILPPool)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'
	# Assert the correct outputs
	results = milp.generate_outputs()
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	results['c_ind2pool'] = round_cost(results['c_ind2pool'])
	results['c_ind2pool_without_deg'] = round_cost(results['c_ind2pool_without_deg'])
	results['c_ind2pool_without_deg_and_p_extra'] = round_cost(results['c_ind2pool_without_deg_and_p_extra'])
	results['c_ind2pool_without_p_extra'] = round_cost(results['c_ind2pool_without_p_extra'])
	results['dual_prices'] = [round(dp, 3) for dp in results['dual_prices']]
	for ki, valu in results.items():
		assert valu == OUTPUTS_S2_POOL_HVAC.get(ki), f'{ki}'

if __name__ == '__main__':
	test_solve_collective_pool_milp()
