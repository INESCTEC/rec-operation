import multiprocessing as mp

from rec_op_lem_prices.optimization.module.IndividualCost import calculate_individual_cost
from rec_op_lem_prices.optimization.module.StageOneMILP import StageOneMILP
from rec_op_lem_prices.optimization.module.StageTwoMILPBilateral import StageTwoMILPBilateral
from rec_op_lem_prices.optimization.module.StageTwoMILPPool import StageTwoMILPPool
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
from joblib import Parallel, delayed
from loguru import logger


# --- FOR PRE-DELIVERY TIMEFRAME ---------------------------------------------------------------------------------------
def run_pre_individual_milp(backpack: BackpackS1Dict) \
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
	}
	"""
	logger.info(f'Running a pre-delivery individual MILP ({backpack["id"]})...')

	milp = StageOneMILP(backpack)
	milp.solve_milp()
	results = milp.generate_outputs()

	logger.info(f'Running a pre-delivery individual MILP ({backpack["id"]})... DONE!')

	return results


def run_pre_single_stage_collective_pool_milp(backpack: SinglePreBackpackS2PoolDict) \
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

	milp = StageTwoMILPPool(backpack)
	milp.solve_milp()
	results = milp.generate_outputs()

	logger.info('Running a pre-delivery standalone/second stage collective (pool) MILP... DONE!')

	return results


def run_pre_single_stage_collective_bilateral_milp(backpack: SinglePreBackpackS2BilateralDict) \
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

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0

	milp = StageTwoMILPBilateral(backpack)
	milp.solve_milp()
	results = milp.generate_outputs()

	logger.info('Running a pre-delivery standalone/second stage collective (bilateral) MILP... DONE!')

	return results


def run_pre_two_stage_collective_pool_milp(backpack: CollectivePreBackpackS2PoolDict, for_testing=False) \
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
	:return: a tuple with first, the collective optimization results, as provided in
		"run_pre_single_stage_collective_pool_milp" and second, a list with the results from the individual
		optimization stages, as provided in "run_pre_individual_milp".
	"""
	logger.info('Running a pre-delivery two-stage collective (pool) MILP...')

	# Set values for specific run
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data['btm_storage'],
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
		delayed(run_pre_individual_milp)(ind_backpack) for ind_backpack in individual_backpacks)

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
	milp = StageTwoMILPPool(backpack)
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


def run_pre_two_stage_collective_bilateral_milp(backpack: CollectivePreBackpackS2BilateralDict, for_testing=False) \
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
	:return: a tuple with first, the collective optimization results, as provided in
		"run_pre_single_stage_collective_bilateral_milp" and second, a list with the results from the individual
		optimization stages, as provided in "run_pre_individual_milp".
	"""
	logger.info('Running a pre-delivery two-stage collective (bilateral) MILP...')

	# Set values for specific run
	backpack['second_stage'] = True

	# Prepare the inputs for the individual optimization stages according to BackpackS1Dict
	individual_backpacks = []
	for meter_name, meter_data in backpack['meters'].items():
		ind_bp = {
			'btm_storage': meter_data['btm_storage'],
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
		delayed(run_pre_individual_milp)(ind_backpack) for ind_backpack in individual_backpacks)

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
	milp = StageTwoMILPBilateral(backpack)
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


def run_post_single_stage_collective_pool_milp(backpack: SinglePostBackpackS2PoolDict) \
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

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	milp = StageTwoMILPPool(backpack)
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


def run_post_single_stage_collective_bilateral_milp(backpack: SinglePostBackpackS2BilateralDict) \
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

	# Set values for specific run
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	milp = StageTwoMILPBilateral(backpack)
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


def run_post_two_stage_collective_pool_milp(backpack: CollectivePostBackpackS2PoolDict, for_testing=False) \
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
	:return: a tuple with first, the collective optimization results, as provided in
		"run_post_single_stage_collective_pool_milp" and second, a list with the results from the individual
		cost computations, as provided in "run_post_individual_cost".
	"""
	logger.info('Running a post-delivery two-stage collective (pool) MILP...')

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
	milp = StageTwoMILPPool(backpack)
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


def run_post_two_stage_collective_bilateral_milp(backpack: CollectivePostBackpackS2BilateralDict, for_testing=False) \
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
	:return: a tuple with first, the collective optimization results, as provided in
		"run_post_single_stage_collective_bilateral_milp" and second, a list with the results from the individual
		cost computations, as provided in "run_post_individual_cost".
	"""
	logger.info('Running a post-delivery two-stage collective (bilateral) MILP...')

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
	milp = StageTwoMILPBilateral(backpack)
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
