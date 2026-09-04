import multiprocessing as mp
import numpy as np

from rec_op_lem_prices.optimization.module.IndividualCost import calculate_individual_cost
from rec_op_lem_prices.optimization.module.StageOneMILP import StageOneMILP
from rec_op_lem_prices.optimization.module.StageTwoMILPBilateral import StageTwoMILPBilateral
from rec_op_lem_prices.optimization.module.StageTwoMILPPool import StageTwoMILPPool
from rec_op_lem_prices.optimization.module.StageThreeMILPPool import StageThreeMILPPool
from rec_op_lem_prices.optimization.module.StageThreeMILPPoolAct import StageThreeMILPPoolAct
from rec_op_lem_prices.custom_types.individual_cost_types import (
	BackpackIndCostDict,
	OutputsIndCostDict
)
from rec_op_lem_prices.custom_types.stage_one_milp_types import (
	BackpackS1Dict,
	OutputsS1Dict
)
from rec_op_lem_prices.custom_types.stage_two_milp_bilateral_types import (
	CollectivePostBackpackS2BilateralDict,
	CollectivePostOutputsS2BilateralDict,
	CollectivePreBackpackS2BilateralDict,
	CollectivePreOutputsS2BilateralDict,
	SinglePostBackpackS2BilateralDict,
	SinglePreBackpackS2BilateralDict,
	SinglePostOutputsS2BilateralDict,
	SinglePreOutputsS2BilateralDict
)
from rec_op_lem_prices.custom_types.stage_two_milp_pool_types import (
	CollectivePostBackpackS2PoolDict,
	CollectivePostOutputsS2PoolDict,
	CollectivePreBackpackS2PoolDict,
	CollectivePreOutputsS2PoolDict,
	SinglePostBackpackS2PoolDict,
	SinglePostOutputsS2PoolDict,
	SinglePreBackpackS2PoolDict,
	SinglePreOutputsS2PoolDict
)
from rec_op_lem_prices.custom_types.stage_three_milp_pool_types import (
	# CollectivePostBackpackS3PoolDict,
	# CollectivePostOutputsS3PoolDict,
	CollectivePreBackpackS3PoolDict,
	CollectivePreOutputsS3PoolDict,
	# SinglePostBackpackS3PoolDict,
	# SinglePostOutputsS3PoolDict,
	# SinglePreBackpackS3PoolDict,
	# SinglePreOutputsS3PoolDict
)

from joblib import Parallel, delayed
from loguru import logger
from pulp import listSolvers


AVAILABLE_SOLVERS = {
    "CPLEX": "CPLEX_CMD" in listSolvers(onlyAvailable=True),
    "GUROBI": "GUROBI_CMD" in listSolvers(onlyAvailable=True),
}


# --- FOR PRE-DELIVERY TIMEFRAME ---------------------------------------------------------------------------------------
def run_pre_individual_milp(backpack: BackpackS1Dict, solver='CBC') \
		-> OutputsS1Dict:
	"""
	Use this function to compute an individual MILP (stage 1) for a given Meter, community member, microgrid or
	hybrid park.
	This function is specific for a pre-delivery timeframe, providing the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets) for hours- or
	day-ahead.
	The function requires the provision of several forecasts, parameters and other data which thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'btm_storage': structure where several Btm BESS units can be defined
		{
			#storage_id: {
				'degradation_cost': a fictitious cost in €/kWh that penalizes the storage usage
				'e_bn': the storage current or initial nominal capacity, in kWh
				'eff_bc': a fixed value, between 0 and 1, that expresses the charging efficiency of the BESS
				'eff_bd': a fixed value, between 0 and 1, that expresses the discharging efficiency of the BESS
				'init_e': the initial energy content of the storage unit, in kWh
				'p_max': the maximum charge/discharge power that can be set, in kW
				'soc_max': a percentage, applicable to "e_bn", identifying a maximum limit to the energy content
				'soc_min': a percentage, applicable to "e_bn", identifying a minimum limit to the energy content
			}
		}
		'btm_evs': structure where several Btm EVs units can be defined
		{
			#EV_id: {
				'trip_ev': EV energy consumption, in kWh
				'min_energy_storage_ev': Minimum stored energy to be guaranteed for vehicle ev at CPE n, in kWh
				'battery_capacity_ev': The battery energy capacity of vehicle ev at CPE n, in kWh
				'eff_bc_ev': Charging efficiency of vehicle ev at CPE n, between 0 and 1
				'eff_bd_ev': Discharging efficiency of vehicle ev at CPE n, between 0 and 1
				'init_e_ev': the initial energy content of the EV, in kWh
				'pmax_c_ev': Maximum power charge of vehicle ev at CPE n, in kW
				'pmax_d_ev': Maximum power discharge of vehicle ev at CPE n, in kW
				'bin_ev': Whether a vehicle ev at CPE n is plugged-in or not (if plugged-in = 1 else = 0)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'e_c': an array with the forecasted Btm total energy consumption, in kWh
		'e_g': an array with the forecasted Btm total energy generation, in kWh
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'id': a string that unequivocally identifies the Meter, member, microgrid or hybrid park for which the problem
			is being solved
		'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
		'max_p': maximum admissible power at the connection with the grid, in kW (e.g., can be the contracted power)
	}
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: {
		'c_ind': float with the individual cost with energy for the optimization horizon, in €;
			positive values are costs, negative values are profits
		'c_ind_without_deg': same as "c_ind" without the degradation cost, in €
		'c_ind_without_deg_and_p_extra':  same as "c_ind" without the degradation cost and power limit violation cost,
			in €
		'c_ind_without_p_extra': same as "c_ind" without the power limit violation cost, in €
		'meter_id': string with the identification of the Meter, member, microgrid or hybrid park
		'deg_cost': float with the batteries' total degradation cost, in €
		'delta_bc': array with auxiliary binary values
		'delta_sup': array with auxiliary binary values
		'e_bat': dict of arrays with the evolution of the energy content of each storage asset, in kWh
		'e_bc': dict of arrays with the charging energy setpoints for each storage asset, in kWh
		'e_bd': dict of arrays with the discharging energy setpoints for each storage asset, in kWh
		'e_cmet': array with the net load consumption forecasted after using the BESS, in kWh
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'milp_status': string with the status of the optimization problem; only non-error value is "Optimal"
		'obj_value': value obtained for the objective function under an optimal solution of the MILP
		'p_extra': array with the extra power consumed (positive) or injected (negative) beyond the maximum admissible
			power limit at the connection point with the grid, in kW
		'p_extra_cost': float with the total power limit violation cost, in €
		'soc_bat': dict of arrays with the evolution of the SoC of each storage asset, in %
		'ev_stored': dict of arrays with the EV energy content, in kWh
		'p_ev_charge': dict of arrays with the EV charged, in kW
		'p_ev_discharge': dict of arrays with the EV discharged, in kW
	}
	"""
	logger.info(f'Running a pre-delivery individual MILP ({backpack["id"]})...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	milp = StageOneMILP(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()

	logger.info(f'Running a pre-delivery individual MILP ({backpack["id"]})... DONE!')

	return results


def run_pre_single_stage_collective_pool_milp(backpack: SinglePreBackpackS2PoolDict, solver='CBC') \
		-> SinglePreOutputsS2PoolDict:
	"""
	Use this function to compute a standalone collective MILP for a given renewable energy community (REC)
	under a pool market structure.
	This function is specific for a pre-delivery timeframe, providing the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets) for hours- or
	day-ahead.
	The function requires the provision of several forecasts, parameters and other data which thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'btm_storage': structure where several Btm BESS units can be defined
				{
					#storage_id: {
						'degradation_cost': a fictitious cost in €/kWh that penalizes the storage usage
						'e_bn': the storage current or initial nominal capacity, in kWh
						'eff_bc': a fixed value, between 0 and 1, that expresses the charging efficiency of the BESS
						'eff_bd': a fixed value, between 0 and 1, that expresses the discharging efficiency of the BESS
						'init_e': the initial energy content of the storage unit, in kWh
						'p_max': the maximum charge/discharge power that can be set, in kW
						'soc_max': a percentage, applicable to "e_bn", identifying a maximum limit to the energy content
						'soc_min': a percentage, applicable to "e_bn", identifying a minimum limit to the energy content
					}
				}
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
				'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
		'l_lem': an array with the local energy market prices for transacting energy among members, in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'strict_pos_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to be strictly positive (as the Portuguese legislation currently demands)
			or not
		'total_share_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to sum up to 1 (as the Portuguese legislation currently demands)
			or not; this means that if a meter has surplus and it is injecting in the grid, that surplus must totally
			shared with all members of the REC
	}
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: {
		'c_ind2pool': dict of floats with the individual costs with energy for the optimization horizon, in €;
			positive values are costs, negative values are profits
		'c_ind2pool_without_deg': same as "c_ind2pool" without the degradation costs, in €
		'c_ind2pool_without_deg_and_p_extra':  same as "c_ind2pool" without the degradation costs and
			power limit violation costs, in €
		'c_ind2pool_without_p_extra': same as "c_ind2pool" without the power limit violation costs, in €
		'deg_cost2pool': dict of floats with the batteries' total degradation cost, in €
		'delta_alc': dict of arrays with auxiliary binary values
		'delta_bc': dict of arrays with auxiliary binary values
		'delta_cmet': dict of arrays with auxiliary binary values
		'delta_coeff': dict of arrays with auxiliary binary values
		'delta_slc': dict of arrays with auxiliary binary values
		'delta_sup': dict of arrays with auxiliary binary values
		'dual_prices: array with the market equilibrium shadow prices to be used as LEM prices, in €/kWh
		'e_alc': dict of arrays with the allocated energies to each Meter / member, in kWh
		'e_bat': dict of dict of arrays with the evolution of the energy content of each storage asset, in kWh
		'e_bc': dict of dict of arrays with the charging energy setpoints for each storage asset, in kWh
		'e_bd': dict of dict of arrays with the discharging energy setpoints for each storage asset, in kWh
		'e_cmet': dict of arrays with the net load consumptions forecasted after using the BESS, in kWh
		'e_consumed': dict of arrays with the forecasted energy consumptions from the retailer, in kWh
		'e_pur_pool': dict of arrays with the scheduled total energies bought on the LEM, in kWh
		'e_sale_pool': dict of arrays with the scheduled total energies sold on the LEM, in kWh
		'e_slc_pool': dict of arrays with the self-consumed energies from the REC, in kWh
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'milp_status': string with the status of the optimization problem; only non-error value is "Optimal"
		'obj_value': value obtained for the objective function under an optimal solution of the MILP
		'p_extra': dict of arrays with the extra power consumed (positive) or injected (negative) beyond the maximum
			admissible power limit at the connection points with the grid, in kW
		'p_extra_cost2pool': dict of floats with the total power limit violation costs, in €
		'soc_bat': dict of arrays with the evolution of the SoC of each storage asset, in %
	}
	"""
	logger.info('Running a pre-delivery standalone/second stage collective (pool) MILP...')

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()

	logger.info('Running a pre-delivery standalone/second stage collective (pool) MILP... DONE!')

	return results


def run_pre_single_stage_collective_bilateral_milp(backpack: SinglePreBackpackS2BilateralDict, solver='CBC') \
		-> SinglePreOutputsS2BilateralDict:
	"""
	Use this function to compute a standalone collective MILP for a given renewable energy community (REC),
	under a p2p market structure, based on bilateral contracts.
	This function is specific for a pre-delivery timeframe, providing the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets) for hours- or
	day-ahead.
	The function requires the provision of several forecasts, parameters and other data which thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'btm_storage': structure where several Btm BESS units can be defined
				{
					#storage_id: {
						'degradation_cost': a fictitious cost in €/kWh that penalizes the storage usage
						'e_bn': the storage current or initial nominal capacity, in kWh
						'eff_bc': a fixed value, between 0 and 1, that expresses the charging efficiency of the BESS
						'eff_bd': a fixed value, between 0 and 1, that expresses the discharging efficiency of the BESS
						'init_e': the initial energy content of the storage unit, in kWh
						'p_max': the maximum charge/discharge power that can be set, in kW
						'soc_max': a percentage, applicable to "e_bn", identifying a maximum limit to the energy content
						'soc_min': a percentage, applicable to "e_bn", identifying a minimum limit to the energy content
					}
				}
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
				'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': dict of dict of arrays with the applicable tariffs for self-consumed energy between
			pairs of Meters / REC members, in €/kWh
		'l_lem': an array with the local energy market prices for transacting energy among members, in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'strict_pos_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to be strictly positive (as the Portuguese legislation currently demands)
			or not
		'total_share_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to sum up to 1 (as the Portuguese legislation currently demands)
			or not; this means that if a meter has surplus and it is injecting in the grid, that surplus must totally
			shared with all members of the REC
	}
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: {
		'c_ind2bilateral': dict of floats with the individual costs with energy for the optimization horizon, in €;
			positive values are costs, negative values are profits
		'c_ind2bilateral_without_deg': same as "c_ind2bilateral" without the degradation costs, in €
		'c_ind2bilateral_without_deg_and_p_extra':  same as "c_ind2bilateral" without the degradation costs and
			power limit violation costs, in €
		'c_ind2bilateral_without_p_extra': same as "c_ind2bilateral" without the power limit violation costs, in €
		'deg_cost2bilateral': dict of floats with the batteries' total degradation cost, in €
		'delta_alc': dict of arrays with auxiliary binary values
		'delta_bc': dict of arrays with auxiliary binary values
		'delta_cmet': dict of arrays with auxiliary binary values
		'delta_coeff': dict of arrays with auxiliary binary values
		'delta_slc': dict of arrays with auxiliary binary values
		'delta_sup': dict of arrays with auxiliary binary values
		'e_alc': dict of arrays with the allocated energies to each Meter / member, in kWh
		'e_bat': dict of dict of arrays with the evolution of the energy content of each storage asset, in kWh
		'e_bc': dict of dict of arrays with the charging energy setpoints for each storage asset, in kWh
		'e_bd': dict of dict of arrays with the discharging energy setpoints for each storage asset, in kWh
		'e_cmet': dict of arrays with the net load consumptions forecasted after using the BESS, in kWh
		'e_consumed': dict of arrays with the forecasted energy consumptions from the retailer, in kWh
		'e_pur_bilateral': dict of dict of arrays with the scheduled energies bought on the LEM
			between each pair of members, in kWh
		'e_sale_bilateral': dict of dict of arrays with the scheduled total energies sold on the LEM
			between each pair of members, in kWh
		'e_slc_bilateral': dict fo dict of arrays with the self-consumed energies from the REC
			between each pair of members, in kWh
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'milp_status': string with the status of the optimization problem; only non-error value is "Optimal"
		'obj_value': value obtained for the objective function under an optimal solution of the MILP
		'p_extra': dict of arrays with the extra power consumed (positive) or injected (negative) beyond the maximum
			admissible power limit at the connection points with the grid, in kW
		'p_extra_cost2bilateral': dict of floats with the total power limit violation costs, in €
		'soc_bat': dict of arrays with the evolution of the SoC of each storage asset, in %
	}
	"""
	logger.info('Running a pre-delivery standalone/second stage collective (bilateral) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0

	milp = StageTwoMILPBilateral(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()

	logger.info('Running a pre-delivery standalone/second stage collective (bilateral) MILP... DONE!')

	return results


def run_pre_two_stage_collective_pool_milp(backpack: CollectivePreBackpackS2PoolDict, for_testing=False, solver='CBC') \
		-> CollectivePreOutputsS2PoolDict:
	"""
	Use this function to compute the two-step collective MILP for a given renewable energy community (REC)
	under a pool market structure.
	This function is specific for a pre-delivery timeframe, providing the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets) for hours- or
	day-ahead.
	The function requires the provision of several forecasts, parameters and other data which thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: the same inputs used for "run_pre_single_stage_collective_pool_milp"
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: a tuple with first, the collective optimization results, as provided in
		"run_pre_single_stage_collective_pool_milp" and second, a list with the results from the individual
		optimization stages, as provided in "run_pre_individual_milp".
	"""
	logger.info('Running a pre-delivery two-stage collective (pool) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data['btm_storage'],
			'btm_evs': meter_data['btm_evs'],
			'ewh': meter_data['ewh'],
			'delta_t': backpack['delta_t'],
			'e_c': meter_data['e_c'],
			'e_g': meter_data['e_g'],
			'horizon': backpack['horizon'],
			'id': meter_name,
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p']
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
		delayed(run_pre_individual_milp)(ind_backpack, valid_solver) for ind_backpack in individual_backpacks)

	# Check if all individual stages were successfully run
	missing_outputs = any(not output for output in stage1_outputs)
	if missing_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 1. ' \
					'At least one of the individual optimization procedures were unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	not_optimal = {output['meter_id']: output['milp_status']
				   for output in stage1_outputs if output['milp_status'] != 'Optimal'}
	if not_optimal:
		error_msg = f'The following individual optimization procedures were not optimally solved: {not_optimal}. ' \
					f'Please try making another request, verifying all input data. ' \
					f'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	logger.info('Running a pre-delivery two-stage collective (pool) MILP... DONE!')

	return stage2_outputs, stage1_outputs


def run_pre_two_stage_collective_bilateral_milp(backpack: CollectivePreBackpackS2BilateralDict, for_testing=False,
												solver='CBC') \
		-> CollectivePreOutputsS2BilateralDict:
	"""
	Use this function to compute the two-step collective MILP for a given renewable energy community (REC)
	under a p2p market structure, based on bilateral contracts.
	This function is specific for a pre-delivery timeframe, providing the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets) for hours- or
	day-ahead.
	The function requires the provision of several forecasts, parameters and other data which thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: the same inputs used for "run_pre_single_stage_collective_bilateral_milp"
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: a tuple with first, the collective optimization results, as provided in
		"run_pre_single_stage_collective_bilateral_milp" and second, a list with the results from the individual
		optimization stages, as provided in "run_pre_individual_milp".
	"""
	logger.info('Running a pre-delivery two-stage collective (bilateral) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data['btm_storage'],
			'btm_evs': meter_data['btm_evs'],
			'ewh': meter_data['ewh'],
			'delta_t': backpack['delta_t'],
			'e_c': meter_data['e_c'],
			'e_g': meter_data['e_g'],
			'horizon': backpack['horizon'],
			'id': meter_name,
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p']
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
		delayed(run_pre_individual_milp)(ind_backpack, solver) for ind_backpack in individual_backpacks)

	# Check if all individual stages were successfully run
	missing_outputs = any(not output for output in stage1_outputs)
	if missing_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 1. ' \
					'At least one of the individual optimization procedures were unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	not_optimal = {output['meter_id']: output['milp_status']
				   for output in stage1_outputs if output['milp_status'] != 'Optimal'}
	if not_optimal:
		error_msg = f'The following individual optimization procedures were not optimally solved: {not_optimal}. ' \
					f'Please try making another request, verifying all input data. ' \
					f'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPBilateral(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	logger.info('Running a pre-delivery two-stage collective (bilateral) MILP... DONE!')

	return stage2_outputs, stage1_outputs


# --- FOR POST-DELIVERY TIMEFRAME --------------------------------------------------------------------------------------
def run_post_individual_cost(backpack: BackpackIndCostDict) \
		-> OutputsIndCostDict:
	"""
	Use this function to compute the individual operation costs (equivalent to a stage 1 MILP) for a given Meter,
	community member, microgrid or hybrid park.
	This function is specific for a post-delivery timeframe, and all data is historical.
	The function requires the provision of several historical data thoroughly described	below,
	under the parameter "backpack". Arrays with time-varying data such as consumption/generation and
	opportunity costs must have the same length, i.e., the same time step and horizon.
	:param backpack: {
		'delta_t': a float or int with the time step of the historical data arrays, in hours
		'e_met': an array with the measured net consumption (positive = imported; negative = exported), in kWh
		'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
		'id': a string that unequivocally identifies the Meter, member, microgrid or hybrid park for which the problem
			is being solved
		'max_p': float with the maximum admissible power at the connection with the grid, in kW
			(e.g., can be the contracted power)
	}
	:return: {
		'c_ind': float with the individual cost with energy for the whole horizon, in €;
			positive values are costs, negative values are profits
		'meter_id': string with the identification of the Meter, member, microgrid or hybrid park
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'p_extra': array with the extra power consumed (positive) or injected (negative) beyond the maximum admissible
			power limit at the connection point with the grid, in kW
	}
	"""
	logger.info(f'Calculating the individual post-delivery operation costs ({backpack["id"]})...')

	results = calculate_individual_cost(backpack)

	logger.info(f'Calculating the individual post-delivery operation costs ({backpack["id"]})... DONE!')

	return results


def run_post_single_stage_collective_pool_milp(backpack: SinglePostBackpackS2PoolDict, solver='CBC') \
		-> SinglePostOutputsS2PoolDict:
	"""
	Use this function to compute a standalone collective MILP for a given renewable energy community (REC)
	under a pool market structure.
	This function is specific for a post-delivery timeframe, and all data is historical.
	The function requires the provision of several historical data thoroughly described	below,
	under the parameter "backpack". Arrays with time-varying data such as consumption/generation and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
				'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
		'l_lem': an array with the local energy market prices for transacting energy among members, in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'strict_pos_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to be strictly positive (as the Portuguese legislation currently demands)
			or not
		'total_share_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to sum up to 1 (as the Portuguese legislation currently demands)
			or not; this means that if a meter has surplus and it is injecting in the grid, that surplus must totally
			shared with all members of the REC
	}
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: {
		'c_ind2pool': dict of floats with the individual costs with energy for the optimization horizon, in €;
			positive values are costs, negative values are profits
		'c_ind2pool_without_p_extra': same as "c_ind2pool" without the power limit violation costs, in €
		'delta_alc': dict of arrays with auxiliary binary values
		'delta_cmet': dict of arrays with auxiliary binary values
		'delta_coeff': dict of arrays with auxiliary binary values
		'delta_slc': dict of arrays with auxiliary binary values
		'delta_sup': dict of arrays with auxiliary binary values
		'dual_prices: array with the market equilibrium shadow prices to be used as LEM prices, in €/kWh
		'e_alc': dict of arrays with the allocated energies to each Meter / member, in kWh
		'e_cmet': dict of arrays with the net load consumptions forecasted after using the BESS, in kWh
		'e_consumed': dict of arrays with the forecasted energy consumptions from the retailer, in kWh
		'e_pur_pool': dict of arrays with the scheduled total energies bought on the LEM, in kWh
		'e_sale_pool': dict of arrays with the scheduled total energies sold on the LEM, in kWh
		'e_slc_pool': dict of arrays with the self-consumed energies from the REC, in kWh
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'milp_status': string with the status of the optimization problem; only non-error value is "Optimal"
		'obj_value': value obtained for the objective function under an optimal solution of the MILP
		'p_extra': dict of arrays with the extra power consumed (positive) or injected (negative) beyond the maximum
			admissible power limit at the connection points with the grid, in kW
		'p_extra_cost2pool': dict of floats with the total power limit violation costs, in €
	}
	"""
	logger.info('Running a post-delivery standalone/second stage collective (pool) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()

	# Remove non-necessary outputs
	del results['e_bat']
	del results['soc_bat']
	del results['e_bc']
	del results['e_bd']
	del results['delta_bc']
	del results['c_ind2pool_without_deg']
	del results['c_ind2pool_without_deg_and_p_extra']
	del results['deg_cost2pool']

	logger.info('Running a post-delivery standalone/second stage collective (pool) MILP... DONE!')

	return results


def run_post_single_stage_collective_bilateral_milp(backpack: SinglePostBackpackS2BilateralDict, solver='CBC') \
		-> SinglePostOutputsS2BilateralDict:
	"""
	Use this function to compute a standalone collective MILP for a given renewable energy community (REC),
	under a p2p market structure, based on bilateral contracts.
	This function is specific for a post-delivery timeframe, and all data is historical.
	The function requires the provision of several historical data thoroughly described	below,
	under the parameter "backpack". Arrays with time-varying data such as consumption/generation and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
				'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
		'l_lem': an array with the local energy market prices for transacting energy among members, in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'strict_pos_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to be strictly positive (as the Portuguese legislation currently demands)
			or not
		'total_share_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to sum up to 1 (as the Portuguese legislation currently demands)
			or not; this means that if a meter has surplus and it is injecting in the grid, that surplus must totally
			shared with all members of the REC
	}
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: {
		'c_ind2bilateral': dict of floats with the individual costs with energy for the optimization horizon, in €;
			positive values are costs, negative values are profits
		'c_ind2bilateral_without_p_extra': same as "c_ind2bilateral" without the power limit violation costs, in €
		'delta_alc': dict of arrays with auxiliary binary values
		'delta_cmet': dict of arrays with auxiliary binary values
		'delta_coeff': dict of arrays with auxiliary binary values
		'delta_slc': dict of arrays with auxiliary binary values
		'delta_sup': dict of arrays with auxiliary binary values
		'e_alc': dict of arrays with the allocated energies to each Meter / member, in kWh
		'e_cmet': dict of arrays with the net load consumptions forecasted after using the BESS, in kWh
		'e_consumed': dict of arrays with the forecasted energy consumptions from the retailer, in kWh
		'e_pur_bilateral': dict of arrays with the scheduled total energies bought on the LEM, in kWh
		'e_sale_bilateral': dict of arrays with the scheduled total energies sold on the LEM, in kWh
		'e_slc_bilateral': dict of arrays with the self-consumed energies from the REC, in kWh
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'milp_status': string with the status of the optimization problem; only non-error value is "Optimal"
		'obj_value': value obtained for the objective function under an optimal solution of the MILP
		'p_extra': dict of arrays with the extra power consumed (positive) or injected (negative) beyond the maximum
			admissible power limit at the connection points with the grid, in kW
		'p_extra_cost2bilateral': dict of floats with the total power limit violation costs, in €
	}
	"""
	logger.info('Running a post-delivery standalone/second stage collective (bilateral) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	milp = StageTwoMILPBilateral(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()

	# Remove non-necessary outputs
	del results['e_bat']
	del results['soc_bat']
	del results['e_bc']
	del results['e_bd']
	del results['delta_bc']
	del results['c_ind2bilateral_without_deg']
	del results['c_ind2bilateral_without_deg_and_p_extra']
	del results['deg_cost2bilateral']

	logger.info('Running a post-delivery standalone/second stage collective (bilateral) MILP... DONE!')

	return results


def run_post_two_stage_collective_pool_milp(backpack: CollectivePostBackpackS2PoolDict, for_testing=False,
											solver='CBC') \
		-> CollectivePostOutputsS2PoolDict:
	"""
	Use this function to compute the two-step collective MILP for a given renewable energy community (REC)
	under a pool market structure.
	This function is specific for a post-delivery timeframe, and all data is historical.
	The function requires the provision of several historical data thoroughly described	below,
	under the parameter "backpack". Arrays with time-varying data such as consumption/generation and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: the same inputs used for "run_post_single_stage_collective_pool_milp"
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: a tuple with first, the collective optimization results, as provided in
		"run_post_single_stage_collective_pool_milp" and second, a list with the results from the individual
		cost computations, as provided in "run_post_individual_cost".
	"""
	logger.info('Running a post-delivery two-stage collective (pool) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = True
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'delta_t': backpack['delta_t'],
			'e_met': [ec - eg for ec, eg in zip(meter_data['e_c'], meter_data['e_g'])],
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p'],
			'id': meter_name
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
		delayed(run_post_individual_cost)(ind_backpack) for ind_backpack in individual_backpacks)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Remove non-necessary outputs
	del stage2_outputs['e_bat']
	del stage2_outputs['soc_bat']
	del stage2_outputs['e_bc']
	del stage2_outputs['e_bd']
	del stage2_outputs['delta_bc']
	del stage2_outputs['c_ind2pool_without_deg']
	del stage2_outputs['c_ind2pool_without_deg_and_p_extra']
	del stage2_outputs['deg_cost2pool']

	logger.info('Running a post-delivery two-stage collective (pool) MILP... DONE!')

	return stage2_outputs, stage1_outputs


def run_post_two_stage_collective_bilateral_milp(backpack: CollectivePostBackpackS2BilateralDict, for_testing=False,
												 solver='CBC') \
		-> CollectivePostOutputsS2BilateralDict:
	"""
	Use this function to compute the two-step collective MILP for a given renewable energy community (REC)
	under a p2p market structure, based on bilateral contracts.
	This function is specific for a post-delivery timeframe, and all data is historical.
	The function requires the provision of several historical data thoroughly described	below,
	under the parameter "backpack". Arrays with time-varying data such as consumption/generation and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: the same inputs used for "run_post_single_stage_collective_bilateral_milp"
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: a tuple with first, the collective optimization results, as provided in
		"run_post_single_stage_collective_bilateral_milp" and second, a list with the results from the individual
		cost computations, as provided in "run_post_individual_cost".
	"""
	logger.info('Running a post-delivery two-stage collective (bilateral) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = True
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'delta_t': backpack['delta_t'],
			'e_met': [ec - eg for ec, eg in zip(meter_data['e_c'], meter_data['e_g'])],
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p'],
			'id': meter_name
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
		delayed(run_post_individual_cost)(ind_backpack) for ind_backpack in individual_backpacks)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPBilateral(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Remove non-necessary outputs
	del stage2_outputs['e_bat']
	del stage2_outputs['soc_bat']
	del stage2_outputs['e_bc']
	del stage2_outputs['e_bd']
	del stage2_outputs['delta_bc']
	del stage2_outputs['c_ind2bilateral_without_deg']
	del stage2_outputs['c_ind2bilateral_without_deg_and_p_extra']
	del stage2_outputs['deg_cost2bilateral']

	logger.info('Running a post-delivery two-stage collective (bilateral) MILP... DONE!')

	return stage2_outputs, stage1_outputs


def run_pre_three_stage_collective_pool_milp(backpack: CollectivePreBackpackS3PoolDict, for_testing=False,solver='CBC') \
		-> CollectivePreOutputsS3PoolDict:
	"""
	Use this function to compute the three-step collective MILP for a given renewable energy community (REC)
	under a pool market structure.
	This function is specific for a pre-delivery timeframe, providing the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets) for hours- or
	day-ahead.
	The function requires the provision of several forecasts, parameters and other data which thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'btm_storage': structure where several Btm BESS units can be defined
				{
					#storage_id: {
						'degradation_cost': a fictitious cost in €/kWh that penalizes the storage usage
						'e_bn': the storage current or initial nominal capacity, in kWh
						'eff_bc': a fixed value, between 0 and 1, that expresses the charging efficiency of the BESS
						'eff_bd': a fixed value, between 0 and 1, that expresses the discharging efficiency of the BESS
						'init_e': the initial energy content of the storage unit, in kWh
						'p_max': the maximum charge/discharge power that can be set, in kW
						'soc_max': a percentage, applicable to "e_bn", identifying a maximum limit to the energy content
						'soc_min': a percentage, applicable to "e_bn", identifying a minimum limit to the energy content
					}
				}
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer, in €/kWh
				'l_sell': an array with the opportunity costs for selling energy to the retailer, in €/kWh
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
		'l_lem': an array with the local energy market prices for transacting energy among members, in €/kWh
		'l_market_buy': an array with market-indexed buying tariffs in €/kWh
		'l_market_sell': an array with market-indexed selling tariffs in €/kWh
		'l_flex': an array with flexibility prices in €/kWh
		't_flex': an array with the periods/hours where flexibility is expected
		't_no_flex': an array with the periods/hours where flexibility is not expected
		'rho_tot': an array with the tolerance for each period/hour
		'strict_pos_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to be strictly positive (as the Portuguese legislation currently demands)
			or not
		'total_share_coeffs': boolean indicating if the (dynamic) allocation coefficients that are generated by the
			internal REC transactions need to sum up to 1 (as the Portuguese legislation currently demands)
			or not; this means that if a meter has surplus and it is injecting in the grid, that surplus must totally
			shared with all members of the REC
	}
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: first, the collective optimization results for stage 3:
		'c_ind3pool': dict of floats with the individual costs with energy for the optimization horizon, in €;
			positive values are costs, negative values are profits
		'c_ind3pool_without_deg': same as "c_ind3pool" without the degradation costs, in €
		'c_ind3pool_without_deg_and_p_extra':  same as "c_ind3pool" without the degradation costs and
			power limit violation costs, in €
		'c_ind3pool_without_p_extra': same as "c_ind3pool" without the power limit violation costs, in €
		'deg_cost3pool': dict of floats with the batteries' total degradation cost, in €
		'delta_alc': dict of arrays with auxiliary binary values
		'delta_bc': dict of arrays with auxiliary binary values
		'delta_cmet': dict of arrays with auxiliary binary values
		'delta_coeff': dict of arrays with auxiliary binary values
		'delta_slc': dict of arrays with auxiliary binary values
		'delta_sup': dict of arrays with auxiliary binary values
		'dual_prices: array with the market equilibrium shadow prices to be used as LEM prices, in €/kWh
		'e_alc': dict of arrays with the allocated energies to each Meter / member, in kWh
		'e_bat': dict of dict of arrays with the evolution of the energy content of each storage asset, in kWh
		'e_bc': dict of dict of arrays with the charging energy setpoints for each storage asset, in kWh
		'e_bd': dict of dict of arrays with the discharging energy setpoints for each storage asset, in kWh
		'e_cmet': dict of arrays with the net load consumptions forecasted after using the BESS, in kWh
		'e_flex': dict of arrays with the flexibility provided, in kWh
		'e_gg': dict of arrays with the actual generation (forecasted - curtailed), in kWh
		'e_curt': dict of arrays with the curtailed generation, in kWh
		'e_consumed': dict of arrays with the forecasted energy consumptions from the retailer, in kWh
		'e_pur_pool': dict of arrays with the scheduled total energies bought on the LEM, in kWh
		'e_sale_pool': dict of arrays with the scheduled total energies sold on the LEM, in kWh
		'e_slc_pool': dict of arrays with the self-consumed energies from the REC, in kWh
		'e_sup_market': array with energy bought at market-indexed buying tariff, in kWh
		'e_sup_retail': array with energy bought at the retailer opportunity costs, in kWh
		'e_sur_market': array with energy sold at market-indexed selling tariff, in kW,
		'e_sur_retail': array with energy sold at the retailer opportunity costs, in kWh
		'milp_status': string with the status of the optimization problem; only non-error value is "Optimal"
		'obj_value': value obtained for the objective function under an optimal solution of the MILP
		'p_extra': dict of arrays with the extra power consumed (positive) or injected (negative) beyond the maximum
			admissible power limit at the connection points with the grid, in kW
		'p_extra_cost3pool': dict of floats with the total power limit violation costs, in €
		'soc_bat': dict of arrays with the evolution of the SoC of each storage asset, in %

		second, the collective optimization results for stage 2, as provided in
		"run_pre_single_stage_collective_pool_milp" and third, a list with the results from the individual
		optimization stage, as provided in "run_pre_individual_milp".	}
	"""
	logger.info('Running a pre-delivery three-stage collective (pool) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set values for specific run
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data['btm_storage'],
			'btm_evs': meter_data['btm_evs'],
			'ewh': meter_data['ewh'],
			'delta_t': backpack['delta_t'],
			'e_c': meter_data['e_c'],
			'e_g': meter_data['e_g'],
			'horizon': backpack['horizon'],
			'id': meter_name,
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p']
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
		delayed(run_pre_individual_milp)(ind_backpack, solver) for ind_backpack in individual_backpacks)

	# Check if all individual stages were successfully run
	missing_outputs = any(not output for output in stage1_outputs)
	if missing_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 1. ' \
					'At least one of the individual optimization procedures were unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	not_optimal = {output['meter_id']: output['milp_status']
				   for output in stage1_outputs if output['milp_status'] != 'Optimal'}
	if not_optimal:
		error_msg = f'The following individual optimization procedures were not optimally solved: {not_optimal}. ' \
					f'Please try making another request, verifying all input data. ' \
					f'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Set stage values
	backpack['second_stage'] = False
	backpack['third_stage'] = True

	# Add stage2 data (baseline and stage2 indiv costs) to the backpack for stage3
	for meter, values in stage2_outputs["e_cmet"].items():
		backpack["meters"][meter]["e_cmet2"] = values
	for meter, values in stage2_outputs["c_ind2pool"].items():
		backpack["meters"][meter]["c_ind2"] = values

	# Clean t_flex (remove nan values)
	backpack['t_flex'] = [t for t in backpack['t_flex'] if not np.isnan(t)]
	# Calculate t_no_flex
	n_steps = int(round(backpack['horizon'] / backpack['delta_t']))
	t_flex = set(backpack.get('t_flex', []))
	backpack['t_no_flex'] = [i for i in range(n_steps) if i not in t_flex]

	# Run the third stage of optimization
	milp = StageThreeMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	stage3_outputs = milp.generate_outputs()

	# Check if the third stage was successfully run
	if not stage3_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 3. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage3_outputs['milp_status'] if stage3_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 3 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	logger.info('Running a pre-delivery three-stage collective (pool) MILP... DONE!')

	return stage3_outputs, stage2_outputs, stage1_outputs


def run_bidding_curve(backpack: CollectivePreBackpackS3PoolDict, l_flex_ini: float, l_flex_fin: float, l_flex_increment: float, for_testing=False, solver='CBC') \
		-> (CollectivePreOutputsS2PoolDict, list):
	"""
	Use this function to compute the bidding curve for a given renewable energy community (REC)
	under a pool market structure.
	Similar to run_pre_three_stage_collective_pool_milp, but runs stage 3 multiple times for different flexibility
	prices, starting at an  initial flexibility price (l_flex_ini), and up to a maximum price (l_flex_fin), with a
	price increment (l_flex_increment) defined by the user
	:param backpack: the same inputs used for "run_pre_three_stage_collective_pool_milp"
	:param l_flex_ini: the initial flexibility price, in €/kWh
	:param l_flex_fin: the final flexibility price, in €/kWh
	:param l_flex_increment: the increment of the flexibility price, in €/kWh
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: the results of stage 1 and stage 2, and a bid_curve_array, which includes, for each price of flexibility,
	the total amount of flexibility to be provided by the whole REC, and the results of stage 3 for that price (as
	described in "run_pre_three_stage_collective_pool_milp")
	"""
	logger.info('Running bidding curve with a collective (pool) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set stage values
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data['btm_storage'],
			'btm_evs': meter_data['btm_evs'],
			'ewh': meter_data['ewh'],
			'delta_t': backpack['delta_t'],
			'e_c': meter_data['e_c'],
			'e_g': meter_data['e_g'],
			'horizon': backpack['horizon'],
			'id': meter_name,
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p']
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
		delayed(run_pre_individual_milp)(ind_backpack, solver) for ind_backpack in individual_backpacks)

	# Check if all individual stages were successfully run
	missing_outputs = any(not output for output in stage1_outputs)
	if missing_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 1. ' \
					'At least one of the individual optimization procedures were unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	not_optimal = {output['meter_id']: output['milp_status']
				   for output in stage1_outputs if output['milp_status'] != 'Optimal'}
	if not_optimal:
		error_msg = f'The following individual optimization procedures were not optimally solved: {not_optimal}. ' \
					f'Please try making another request, verifying all input data. ' \
					f'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Set stage values
	backpack['second_stage'] = False
	backpack['third_stage'] = True

	# Add stage2 data (baseline and stage2 indiv costs) to the backpack for stage3
	for meter, values in stage2_outputs["e_cmet"].items():
		backpack["meters"][meter]["e_cmet2"] = values
	for meter, values in stage2_outputs["c_ind2pool"].items():
		backpack["meters"][meter]["c_ind2"] = values

	# Clean t_flex (remove nan values)
	backpack['t_flex'] = [t for t in backpack['t_flex'] if not np.isnan(t)]
	# Calculate t_no_flex
	n_steps = int(round(backpack['horizon'] / backpack['delta_t']))
	t_flex = set(backpack.get('t_flex', []))
	backpack['t_no_flex'] = [i for i in range(n_steps) if i not in t_flex]

	# Set initial flex price (l_flex_ini) (note: comment when using flex prices from input excel)
	backpack['l_flex'] = [0] * int(backpack['horizon'] / backpack['delta_t'])
	# Set initial value for each hour in t_flex
	for hour in backpack['t_flex']:
		backpack['l_flex'][int(hour)] = l_flex_ini

	# Set flex price for first iteration (l_flex_it)
	l_flex_it = l_flex_ini

	# Initialize bid curve array and total flex (of each bid)
	bid_curve_array = []
	sum_e_flex = 0

	while l_flex_it <= l_flex_fin:

		# Run the third stage of optimization
		milp = StageThreeMILPPool(backpack, solver=valid_solver)
		milp.solve_milp()
		stage3_outputs = milp.generate_outputs()

		# Check if the third stage was successfully run
		if not stage3_outputs:
			error_msg = 'The solver has raised an unexpected error during stage 3. ' \
						'The collective optimization procedure was unsuccessful. ' \
						'Please try making another request, verifying all input data. ' \
						'If the problem persists, please contact the developers.'
			raise ValueError(error_msg)

		non_optimal = stage3_outputs['milp_status'] if stage3_outputs['milp_status'] != 'Optimal' else None
		if non_optimal:
			error_msg = f'Stage 3 was not optimally solved: milp_status = {non_optimal}. ' \
						'Please try making another request, verifying all input data. ' \
						'If the problem persists, please contact the developers.'
			raise ValueError(error_msg)

		# Sum e_flex
		for key, value in stage3_outputs['e_flex'].items():
			# Use np.nansum() to sum the values while ignoring NaNs
			sum_e_flex += np.nansum(value)

		# Save sum_e_flex and value of l_flex
		bid_curve_array.append([l_flex_it, sum_e_flex, stage3_outputs])

		# Increment l_flex
		for hour in backpack['t_flex']:
			backpack['l_flex'][int(hour)] += l_flex_increment

		# Increment flex price
		l_flex_it += l_flex_increment
		l_flex_it = round(l_flex_it, 3)

		# Reset total flex of the bid
		sum_e_flex = 0

	logger.info('Running bidding curve with a collective (pool) MILP... DONE!')

	return bid_curve_array, stage2_outputs, stage1_outputs


def bid_activation(backpack: CollectivePreBackpackS3PoolDict, l_flex: float, act_flex: float, for_testing=False, solver='CBC') \
		-> (CollectivePreOutputsS2PoolDict, list):
	"""
	Use this function to.
	:param backpack: the same inputs used for "run_pre_three_stage_collective_pool_milp"
	:param l_flex: flex price of the activated bid"
	:param act_flex: flex submitted in the activated bid"
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: the results of stage 3 for that price and flex (as described in "run_pre_three_stage_collective_pool_milp")
	"""
	logger.info('Running bidding curve with a collective (pool) MILP...')

	# Validate the solver used
	if AVAILABLE_SOLVERS.get(solver, False):
		valid_solver = solver
	else:
		valid_solver = "CBC"
	logger.info(f"Solver: {valid_solver}")

	# Set stage value
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data.get('btm_storage', None),  # Use None as default if 'btm_storage' is not present
			'btm_evs': meter_data.get('btm_evs', None),  # Use None as default if 'btm_evs' is not present
			'ewh': meter_data.get('ewh', None),  # Use None as default if 'ewh' is not present
			'delta_t': backpack['delta_t'],
			'e_c': meter_data['e_c'],
			'e_g': meter_data['e_g'],
			'horizon': backpack['horizon'],
			'id': meter_name,
			'l_buy': meter_data['l_buy'],
			'l_extra': backpack['l_extra'],
			'l_market_buy': backpack['l_market_buy'],
			'l_market_sell': backpack['l_market_sell'],
			'l_sell': meter_data['l_sell'],
			'max_p': meter_data['max_p']
		}
		individual_backpacks.append(ind_bp)

	# Run in parallel the first stage of optimization for all Meters provided
	partitions = mp.cpu_count() if not for_testing else 1
	stage1_outputs = Parallel(n_jobs=partitions, backend='multiprocessing', max_nbytes=None)(
			delayed(run_pre_individual_milp)(ind_backpack, solver) for ind_backpack in individual_backpacks)

	# Check if all individual stages were successfully run
	missing_outputs = any(not output for output in stage1_outputs)
	if missing_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 1. ' \
					'At least one of the individual optimization procedures were unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	not_optimal = {output['meter_id']: output['milp_status']
				   for output in stage1_outputs if output['milp_status'] != 'Optimal'}
	if not_optimal:
		error_msg = f'The following individual optimization procedures were not optimally solved: {not_optimal}. ' \
					f'Please try making another request, verifying all input data. ' \
					f'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Add the individual costs found to the backpack for the collective optimization stage
	for output in stage1_outputs:
		meter_id = output['meter_id']
		c_ind = output['c_ind']
		backpack['meters'][meter_id]['c_ind'] = c_ind

	# Run the second stage of optimization
	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	stage2_outputs = milp.generate_outputs()

	# Check if the second stage was successfully run
	if not stage2_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 2. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage2_outputs['milp_status'] if stage2_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 2 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	# Set stage values
	backpack['second_stage'] = False
	backpack['third_stage'] = True

	# Add stage2 data (baseline and stage2 indiv costs) to the backpack for stage3
	for meter, values in stage2_outputs["e_cmet"].items():
		backpack["meters"][meter]["e_cmet2"] = values
	for meter, values in stage2_outputs["c_ind2pool"].items():
		backpack["meters"][meter]["c_ind2"] = values

	# Clean t_flex (remove nan values)
	backpack['t_flex'] = [t for t in backpack['t_flex'] if not np.isnan(t)]
	# Calculate t_no_flex
	n_steps = int(round(backpack['horizon'] / backpack['delta_t']))
	t_flex = set(backpack.get('t_flex', []))
	backpack['t_no_flex'] = [i for i in range(n_steps) if i not in t_flex]

	# Set flex prices for hours with flex
	backpack['l_flex'] = [0] * int(backpack['horizon'] / backpack['delta_t'])
	for hour in backpack['t_flex']:
		backpack['l_flex'][int(hour)] = l_flex

	# Set total flex to be activated during t_flex
	backpack['act_flex'] = act_flex

	# Run the third stage of optimization
	milp = StageThreeMILPPoolAct(backpack, solver=valid_solver)
	milp.solve_milp()
	stage3_act_outputs = milp.generate_outputs()

	# Check if the third stage was successfully run
	if not stage3_act_outputs:
		error_msg = 'The solver has raised an unexpected error during stage 3. ' \
					'The collective optimization procedure was unsuccessful. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	non_optimal = stage3_act_outputs['milp_status'] if stage3_act_outputs['milp_status'] != 'Optimal' else None
	if non_optimal:
		error_msg = f'Stage 3 was not optimally solved: milp_status = {non_optimal}. ' \
					'Please try making another request, verifying all input data. ' \
					'If the problem persists, please contact the developers.'
		raise ValueError(error_msg)

	logger.info('Running bidding curve activation MILP... DONE!')

	return stage3_act_outputs