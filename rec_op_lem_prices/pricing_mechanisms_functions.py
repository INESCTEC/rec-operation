from rec_op_lem_prices.optimization_functions import (
	run_post_two_stage_collective_bilateral_milp,
	run_post_two_stage_collective_pool_milp,
	run_pre_two_stage_collective_bilateral_milp,
	run_pre_two_stage_collective_pool_milp,
)
from rec_op_lem_prices.optimization.helpers.milp_helpers import time_intervals
from rec_op_lem_prices.optimization.module.StageTwoMILPPool import StageTwoMILPPool
from rec_op_lem_prices.pricing_mechanisms.helpers.pricing_helpers import make_offers
from rec_op_lem_prices.pricing_mechanisms.module.PricingMechanisms import (
	compute_crossing_value,
	compute_mmr,
	compute_pruned_mmr,
	compute_pruned_mmr_plus,
	compute_pruned_sdr,
	compute_pruned_sdr_plus,
	compute_sdr,
	get_accepted_offers,
	stop_criterion
)
from rec_op_lem_prices.custom_types.pricing_mechanims_types import OffersList
from rec_op_lem_prices.custom_types.pricing_mechanisms_functions_types import RequestParams
from rec_op_lem_prices.custom_types.stage_two_milp_bilateral_types import (
	CollectivePostOutputsS2BilateralDict,
	CollectivePreOutputsS2BilateralDict,
	LoopPostBackpackS2BilateralDict,
	LoopPreBackpackS2BilateralDict,
)
from rec_op_lem_prices.custom_types.stage_two_milp_pool_types import (
	CollectivePostOutputsS2PoolDict,
	CollectivePreOutputsS2PoolDict,
	LoopPostBackpackS2PoolDict,
	LoopPreBackpackS2PoolDict,
	OutputsS2PoolDict
)

from loguru import logger
from pulp import listSolvers
from typing import Callable, Union
from typing_extensions import Unpack


IS_CPLEX_AVAILABLE = "CPLEX_CMD" in listSolvers(onlyAvailable=True)


# -- AUXILIARY FUNCTIONS -----------------------------------------------------------------------------------------------
def accepted_offers(buys: OffersList, sells: OffersList) -> tuple[OffersList, OffersList]:
	"""
	Function to screen buy and sell offers' lists, returning only the ones that would be accepted in a market pool;
	Accepted offers can be total or partially accepted, this function does not distinguish between them.
	:param buys: list of the following structures: {'origin': str, 'amount': float, 'value': float}:
		- 'origin' can be used to identify the member that makes the hypothetical offer;
		- 'amount' is used to identify the total energy that comprises the offer, in kWh
		- 'value' represents the price in €/kWh that the member is available to pay for the amount of energy needed; in
		theory this value should be te price that the member would otherwise pay to its retailer
	:param sells: list of the following structures: {'origin': str, 'amount': float, 'value': float},
		- 'origin' can be used to identify the member that makes the hypothetical offer;
		- 'amount' is used to identify the total energy that comprises the offer, in kWh
		- 'value' represents the price in €/kWh that the member is available to receive for the amount of energy
		provided; in theory this value should be te price that the member would otherwise receive from its retailer
	:return: screened buy offers' list and sell offers' list
	"""
	return get_accepted_offers(buys, sells)


# -- VANILLA -----------------------------------------------------------------------------------------------------------
def vanilla_mmr(buys: OffersList,
                sells: OffersList,
                pruned=True,
                divider=0.5) -> float:
	"""
	Function to compute the mid-market rate (MMR) for a single session in time;
	If any of the selling offers has a higher value than any of the buying offers,
	the pool crossing value is returned instead;
	By setting the "pruned" parameter to True (default) the function uses only
	offers that would be cleared on a market pool;
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: list with the same structure of "buys" parameter, but for selling offers
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param divider: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 0.5, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and between 0.0 and 1.0
	:return: calculated price for transactions, in €/kWh
	"""
	assert 0.0 <= divider <= 1.0, 'Please provide a divider value between 0.0 and 1.0.'

	logger.info(f'Computing a {"pruned " if pruned else ""}MMR...')

	if pruned:
		result = compute_pruned_mmr(buys, sells, divider)
	else:
		result = compute_mmr(buys, sells, divider)

	logger.info(f'Computing a {"pruned " if pruned else ""}MMR... DONE!')
	return result


def vanilla_sdr(buys: OffersList,
                sells: OffersList,
                pruned=True,
                compensation=0.0) -> float:
	"""
	Function to compute the supply and demand ratio (SDR), compensated (SDRC) or not,
	for a single session in time;
	If any of the selling offers has a higher value than any of the buying offers,
	the pool crossing value is returned instead;
	By setting the "pruned" parameter to True (default) the function uses only
	offers that would be cleared on a market pool;
	By setting the "compensation" parameter to a value between ]0.0, 1.0],
	the compensated version of the SDR, the SDRC, is instead computed.
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: list with the same structure of "buys" parameter, but for selling offers
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:return: calculated price for transactions, in €/kWh
	"""
	assert 0.0 <= compensation <= 1.0, 'Please provide a compensation value between 0.0 and 1.0.'

	logger.info(f'Computing a {"pruned" if pruned else ""} {"compensated " if compensation > 0 else ""}SDR...')

	if pruned:
		result = compute_pruned_sdr(buys, sells, compensation)
	else:
		result = compute_sdr(buys, sells, compensation)

	logger.info(f'Computing a {"pruned" if pruned else ""} {"compensated " if compensation > 0 else ""}SDR... DONE!')
	return result


def vanilla_crossing_value(buys: OffersList,
                           sells: OffersList,
                           small_increment=0.0) -> float:
	"""
	Function to order the market offers and to calculate the crossing value.
	If set, a small_increment if added to sell offers' values and subtracted to buy offers' values.
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: list with the same structure of "buys" parameter, but for selling offers
	:param small_increment: float to add to buy offers' value and subtract from sell offers' value
	:return: calculated price for transactions, in €/kWh
	"""
	logger.info('Computing a pool market clearing...')

	result = compute_crossing_value(buys, sells, small_increment)

	logger.info('Computing a pool market clearing... DONE!')

	return result


# -- VANILLA PLUS ACCEPTED OFFERS --------------------------------------------------------------------------------------
def vanilla_mmr_plus(buys: OffersList,
					 sells: OffersList,
					 divider=0.5) -> (float, OffersList, OffersList):
	"""
	Exact same function as "vanilla_mmr" with "pruned" hyperparameter set to True,
	but also returns the accepted offers that originated the price.
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: list with the same structure of "buys" parameter, but for selling offers
	:param divider: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 0.5, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and between 0.0 and 1.0
	:return: calculated price for transactions, in €/kWh, along with the accepted offers (buy and sell, respectively)
	that originated the price
	"""
	assert 0.0 <= divider, 'Please provide a divider value between 0.0 and 1.0.'

	logger.info(f'Computing a pruned MMR...')

	result, accepted_buys, accepted_sells = compute_pruned_mmr_plus(buys, sells, divider)

	logger.info(f'Computing a pruned MMR... DONE!')

	return result, accepted_buys, accepted_sells


def vanilla_sdr_plus(buys: OffersList,
					 sells: OffersList,
					 compensation=0.0) -> (float, OffersList, OffersList):
	"""
	Exact same function as "vanilla_crossing_value",
	but also returns the accepted offers that originated the price.
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: list with the same structure of "buys" parameter, but for selling offers
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:return: calculated price for transactions, in €/kWh, along with the accepted offers (buy and sell, respectively)
	that originated the price
	"""
	assert 0.0 <= compensation <= 1.0, 'Please provide a compensation value between 0.0 and 1.0.'

	logger.info(f'Computing a pruned SDR...')

	result, accepted_buys, accepted_sells = compute_pruned_sdr_plus(buys, sells, compensation)

	logger.info(f'Computing a pruned SDR... DONE!')

	return result, accepted_buys, accepted_sells


def vanilla_crossing_value_plus(buys: OffersList,
								sells: OffersList,
								small_increment=0.0) -> (float, OffersList, OffersList):
	"""
	Exact same function as "vanilla_sdr",
	but also returns the accepted offers that originated the price.
	If set, a small_increment if added to sell offers' values and subtracted to buy offers' values.
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: list with the same structure of "buys" parameter, but for selling offers
	:param small_increment: float to add to buy offers' value and subtract from sell offers' value
	:return: calculated price for transactions, in €/kWh, along with the accepted offers (buy and sell, respectively)
	that originated the price
	"""
	logger.info('Computing a pool market clearing...')

	result = compute_crossing_value(buys, sells, small_increment)
	accepted_buys, accepted_sells = get_accepted_offers(buys, sells)

	logger.info('Computing a pool market clearing... DONE!')

	return result, accepted_buys, accepted_sells


# -- DUALS -------------------------------------------------------------------------------------------------------------
def dual_pre_pool(backpack: LoopPreBackpackS2PoolDict, solver='CBC') -> (list[float], OutputsS2PoolDict):
	"""
	Function to compute the LEM prices' array from the market equilibrium constraint shadow values.
	A standalone collective MILP is run, where the costs with energy for the whole REC are computed,
	and the shadow values of the market equilibrium constraint are returned after an optimal solution is achieved.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:return: array of float with the LEM prices computed, plus the full MILP outputs' structure;
		the order of the values in the array follows the same order of the provided data
	"""
	logger.info('Running a pre-delivery standalone pool MILP to retrieve dual LEM prices...')

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	# Set values for specific run
	ti = time_intervals(backpack['horizon'], backpack['delta_t'])
	backpack['l_lem'] = [0.0 for _ in range(ti)]
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0

	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()
	dual_prices = results['dual_prices']

	logger.info('Running a pre-delivery standalone pool MILP to retrieve dual LEM prices... DONE!')

	return dual_prices, results


def dual_post_pool(backpack: LoopPostBackpackS2PoolDict, solver='CBC') -> (list[float], OutputsS2PoolDict):
	"""
	Function to compute the LEM prices' array from the market equilibrium constraint shadow values.
	A standalone collective MILP is run, where the costs with energy for the whole REC are computed,
	and the shadow values of the market equilibrium constraint are returned after an optimal solution is achieved.
	This function is specific for a post-delivery timeframe, which means that only the financial transactions
	(i.e., with the retailers and within markets) are optimized.
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:return: array of float with the LEM prices computed, plus the full MILP outputs' structure;
		the order of the values in the array follows the same order of the provided data
	"""
	logger.info('Running a post-delivery standalone pool MILP to retrieve dual LEM prices...')

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	# Set values for specific run
	ti = time_intervals(backpack['horizon'], backpack['delta_t'])
	backpack['l_lem'] = [0.0 for _ in range(ti)]
	backpack['second_stage'] = False
	for _, val in backpack['meters'].items():
		val['c_ind'] = 0.0
		val['btm_storage'] = {}

	milp = StageTwoMILPPool(backpack, solver=valid_solver)
	milp.solve_milp()
	results = milp.generate_outputs()
	dual_prices = results['dual_prices']

	logger.info('Running a post-delivery standalone pool MILP to retrieve dual LEM prices... DONE!')

	return dual_prices, results


# -- PRE-DELIVERY LOOPS ------------------------------------------------------------------------------------------------
def _common_loop(backpack: LoopPreBackpackS2PoolDict,
                 pricing_func: Callable,
                 optimization_func: Callable,
                 for_testing: False,
				 solver: str,
                 **kwargs: Unpack[RequestParams]) \
		-> (
				list[float],
				Union[float, None],
				int,
				Union[CollectivePreOutputsS2PoolDict, CollectivePreOutputsS2BilateralDict]
		):
	"""
	Iterative overarching algorithm for the pre-delivery timeframe
	:param backpack: data for running the two-stage MILP
	:param pricing_func: market mechanism function to be applied
	:param optimization_func: optimization function to be applied
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:param kwargs: necessary flags or numeric parameters that are required by the passed func
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	# START THE LOOP
	logger.info('Starting loop...')

	# Initialize required data for obtaining the initial offers
	l_market_buy = backpack['l_market_buy']
	l_market_sell = backpack['l_market_sell']
	meters = backpack['meters'].copy()
	for meter_name, meter_data in meters.items():
		meter_data['e_met'] = [c - g for c, g in zip(meter_data['e_c'], meter_data['e_g'])]
	nr_sessions = time_intervals(backpack['horizon'], backpack['delta_t'])

	# Initialize the transaction prices "l_lem" with farfetched values, so that a first iteration is triggered
	l_lem = [10 for _ in range(nr_sessions)]

	# Initialize a list that will keep the prices of all prices from previous iterations
	l_lem_evolution = []

	# Initialize the iteration number and the best iteration results
	it = 0
	of2 = 1E6
	best_of2 = 1E5
	best_l_lem = l_lem.copy()
	criterion = None
	break_while = False  # used when Euclidean distance criterion is met, to break out of inner loop
	milp_results = None  # Initialize the MILP results
	best_milp_results = None

	# Print the initial prices considered
	dynamic_size = lambda val: int(3 - len(str(int(val))))
	str_l_lem = [' ' * dynamic_size(x) + f"{x:.2f}" for x in l_lem]
	logger.info(f'/// Starting P2P prices: {"|".join(str_l_lem)}')

	# Infinite loop; ends when convergence criterion is met.
	while True:
		# Check if the current prices achieved the lowest REC operation cost and if so, update best prices
		if of2 < best_of2:
			best_of2 = of2
			best_l_lem = l_lem.copy()
			best_milp_results = milp_results
		logger.info(f'--- O.F. value: ({round(of2, 3)}) | Best O.F. value: ({round(best_of2, 3)})')

		# Test the Euclidean distance stopping criterion, between all old prices and the new prices
		# If the criterion is met, stop the iteration...
		iter_criteria = []
		for previous_l_lem in l_lem_evolution:
			stop, criterion = stop_criterion(previous_l_lem, l_lem)
			iter_criteria.append(round(criterion, 3))
			if stop:
				# Add the latest LEM prices computed to the iterations' list and break the cycle
				l_lem_evolution.append(l_lem)
				break_while = True
				break
		logger.info(f'/// Criteria: {iter_criteria}')
		if break_while:
			break

		# Otherwise...
		# Update the iteration and test for maximum iteration stopping criteria
		it += 1
		if it > 20:
			# Add the latest LEM prices computed to the iterations' list and break the cycle
			l_lem_evolution.append(l_lem)
			break

		# Otherwise...
		logger.info('################################################################')
		# Build the current offers, order them and calculate the P2P price
		buys, sells = make_offers(meters, nr_sessions, l_market_buy, l_market_sell)

		# Get the last iteration prices for later comparison
		l_lem_evolution.append(l_lem)

		# Calculate new LEM prices
		logger.info(f'Calculating LEM prices for all sessions...')
		l_lem = [pricing_func(buys[t], sells[t], **kwargs) for t in range(nr_sessions)]

		# Validate the outputted LEM prices
		assert isinstance(l_lem, list)
		for price in l_lem:
			assert isinstance(price, Union[float, int])
		assert len(l_lem) == nr_sessions

		# Print the new LEM prices computed
		str_l_lem = [' ' * dynamic_size(x) + f"{x:.2f}" for x in l_lem]
		logger.info('/// Iter ' + ' ' * dynamic_size(it) + f'{it} ' + f'P2P prices: {"|".join(str_l_lem)}')

		# Update the LEM prices in the input data for the optimization procedure
		backpack['l_lem'] = l_lem

		# Run the optimization algorithm
		logger.info(f'Solving MILP...')
		milp_results = optimization_func(backpack, for_testing, solver)

		# Retrieve the new e_met and update "meters" structure
		for meter_name, meter_data in milp_results[0]['e_cmet'].items():
			meters[meter_name]['e_met'] = meter_data

		# Retrieve the new objective function value from the collective optimization,
		# that is associated with the REC total cost of operation
		of2 = milp_results[0]['obj_value']

	# Ready final returned statistics
	criterion = round(criterion, 3) if it <= 20 else None
	it = it if it <= 20 else 20

	# When a stopping criterion is met, return the computed prices
	logger.success(f'Stopped algorithm at iteration {it} with stopping criterion = {criterion}.')

	return best_l_lem, criterion, it, best_milp_results


def loop_pre_pool_mmr(backpack: LoopPreBackpackS2PoolDict,
                      for_testing=False,
                      pruned=True,
                      divider=0.5,
					  solver='CBC') \
		-> (
				list[float],
				Union[float, None],
				int,
				CollectivePreOutputsS2PoolDict
		):
	"""
	Function to compute the LEM prices' array iteratively through the application of the two-stage MILP,
	under a pool market structure, and the MMR mechanism.
	In each iteration, new offers are made that result from the scheduled net loads of each member,
	found after running the two-stage MILP algorithm. Those offers are used to compute the prices of
	each market session in the defined horizon which will trigger a new MILP run. The new LEM prices can
	result in new scheduled offers, hence the need to iterate. The iterative algorithm stops once one of
	two criteria is met: minimum difference between LEM price arrays or maximum number of iterations is met.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param divider: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 0.5, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and between 0.0 and 1.0
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	assert 0.0 <= divider <= 1.0, 'Please provide a divider value between 0.0 and 1.0.'
	pricing_func = compute_pruned_mmr if pruned else compute_mmr
	opt_func = run_pre_two_stage_collective_pool_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_loop(backpack,
	                    pricing_func,
	                    opt_func,
	                    for_testing,
	                    divider=divider,
						solver=valid_solver)


def loop_pre_pool_sdr(backpack: LoopPreBackpackS2PoolDict,
                      for_testing=False,
                      pruned=True,
                      compensation=0.0,
					  solver='CBC') \
		-> (
				list[float],
				Union[float, None],
				int,
				CollectivePreOutputsS2PoolDict
		):
	"""
	Function to compute the LEM prices' array iteratively through the application of the two-stage ,
	under a pool market structure, and the SDR mechanism.
	In each iteration, new offers are made that result from the scheduled net loads of each member,
	found after running the two-stage MILP algorithm. Those offers are used to compute the prices of
	each market session in the defined horizon which will trigger a new MILP run. The new LEM prices can
	result in new scheduled offers, hence the need to iterate. The iterative algorithm stops once one of
	two criteria is met: minimum difference between LEM price arrays or maximum number of iterations is met.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	assert 0.0 <= compensation <= 1.0, 'Please provide a compensation value between 0.0 and 1.0.'
	pricing_func = compute_pruned_sdr if pruned else compute_sdr
	opt_func = run_pre_two_stage_collective_pool_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_loop(backpack,
	                    pricing_func,
	                    opt_func,
	                    for_testing,
	                    compensation=compensation,
						solver=valid_solver)


def loop_pre_pool_crossing_value(backpack: LoopPreBackpackS2PoolDict,
                                 for_testing=False,
                                 small_increment=0.0,
								 solver='CBC') \
		-> (
				list[float],
				Union[float, None],
				int,
				CollectivePreOutputsS2PoolDict
		):
	"""
	Function to compute the LEM prices' array iteratively through the application of the two-stage MILP,
	under a pool market structure, and the clearing of a market pool with the buying and selling resulting offers.
	In each iteration, new offers are made that result from the scheduled net loads of each member,
	found after running the two-stage MILP algorithm. Those offers are used to compute the prices of
	each market session in the defined horizon which will trigger a new MILP run. The new LEM prices can
	result in new scheduled offers, hence the need to iterate. The iterative algorithm stops once one of
	two criteria is met: minimum difference between LEM price arrays or maximum number of iterations is met.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param small_increment: float to add to buy offers' value and subtract from sell offers' value
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	pricing_func = compute_crossing_value
	opt_func = run_pre_two_stage_collective_pool_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_loop(backpack,
	                    pricing_func,
	                    opt_func,
	                    for_testing,
	                    small_increment=small_increment,
						solver=valid_solver)


def loop_pre_bilateral_mmr(backpack: LoopPreBackpackS2BilateralDict,
                           for_testing=False,
                           pruned=True,
                           divider=0.5,
						   solver='CBC') \
		-> (
				list[float],
				Union[float, None],
				int,
				CollectivePreOutputsS2BilateralDict
		):
	"""
	Function to compute the LEM prices' array iteratively through the application of the two-stage MILP,
	under a p2p market structure, based on bilateral contracts, and the MMR mechanism.
	In each iteration, new offers are made that result from the scheduled net loads of each member,
	found after running the two-stage MILP algorithm. Those offers are used to compute the prices of
	each market session in the defined horizon which will trigger a new MILP run. The new LEM prices can
	result in new scheduled offers, hence the need to iterate. The iterative algorithm stops once one of
	two criteria is met: minimum difference between LEM price arrays or maximum number of iterations is met.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': dict of dict of arrays with the applicable tariffs for self-consumed energy between
			pairs of Meters / REC members, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param divider: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 0.5, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and between 0.0 and 1.0
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	assert 0.0 <= divider <= 1.0, 'Please provide a divider value between 0.0 and 1.0.'
	pricing_func = compute_pruned_mmr if pruned else compute_mmr
	opt_func = run_pre_two_stage_collective_bilateral_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_loop(backpack,
	                    pricing_func,
	                    opt_func,
	                    for_testing,
	                    divider=divider,
						solver=valid_solver)


def loop_pre_bilateral_sdr(backpack: LoopPreBackpackS2BilateralDict,
                           for_testing=False,
                           pruned=True,
                           compensation=0.0,
						   solver='CBC') \
		-> (
				list[float],
				Union[float, None],
				int,
				CollectivePreOutputsS2BilateralDict
		):
	"""
	Function to compute the LEM prices' array iteratively through the application of the two-stage ,
	under a p2p market structure, based on bilateral contracts, and the SDR mechanism.
	In each iteration, new offers are made that result from the scheduled net loads of each member,
	found after running the two-stage MILP algorithm. Those offers are used to compute the prices of
	each market session in the defined horizon which will trigger a new MILP run. The new LEM prices can
	result in new scheduled offers, hence the need to iterate. The iterative algorithm stops once one of
	two criteria is met: minimum difference between LEM price arrays or maximum number of iterations is met.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': dict of dict of arrays with the applicable tariffs for self-consumed energy between
			pairs of Meters / REC members, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	assert 0.0 <= compensation <= 1.0, 'Please provide a compensation value between 0.0 and 1.0.'
	pricing_func = compute_pruned_sdr if pruned else compute_sdr
	opt_func = run_pre_two_stage_collective_bilateral_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_loop(backpack,
	                    pricing_func,
	                    opt_func,
	                    for_testing,
	                    compensation=compensation,
						solver=valid_solver)


def loop_pre_bilateral_crossing_value(backpack: LoopPreBackpackS2BilateralDict,
                                      for_testing=False,
                                      small_increment=0.0,
									  solver='CBC') \
		-> (
				list[float],
				Union[float, None],
				int,
				CollectivePreOutputsS2BilateralDict
		):
	"""
	Function to compute the LEM prices' array iteratively through the application of the two-stage MILP,
	under a p2p market structure, based on bilateral contracts, and the clearing of a market pool with
	the buying and selling resulting offers.
	In each iteration, new offers are made that result from the scheduled net loads of each member,
	found after running the two-stage MILP algorithm. Those offers are used to compute the prices of
	each market session in the defined horizon which will trigger a new MILP run. The new LEM prices can
	result in new scheduled offers, hence the need to iterate. The iterative algorithm stops once one of
	two criteria is met: minimum difference between LEM price arrays or maximum number of iterations is met.
	This function is specific for a pre-delivery timeframe, which means that the schedules for controllable assets,
	such as battery energy storage systems (BESS, presently the only modelled controllable assets)
	are decision variables of the MILP.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
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
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': dict of dict of arrays with the applicable tariffs for self-consumed energy between
			pairs of Meters / REC members, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param small_increment: float to add to buy offers' value and subtract from sell offers' value
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed for the best iteration,
			i.e. the iteration with the best objective function value;
			the order of the values in the array follows the same order of the provided data
		- stopping criterion computed through the Euclidean distance between price arrays;
			returned as float if the criterion is met;
			returned as None if the criterion wasn't met, but loop broke by reaching the maximum iteration number
		- number of iterations performed
		- full MILP outputs' structure of the solution with the best objective function value
	"""
	pricing_func = compute_crossing_value
	opt_func = run_pre_two_stage_collective_bilateral_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_loop(backpack,
	                    pricing_func,
	                    opt_func,
	                    for_testing,
	                    small_increment=small_increment,
						solver=valid_solver)


# -- POST-DELIVERY HIGHWAYS --------------------------------------------------------------------------------------------
def _common_highway(backpack: LoopPreBackpackS2PoolDict,
                    pricing_func: Callable,
                    optimization_func: Callable,
                    for_testing: False,
					solver: str,
                    **kwargs: Unpack[RequestParams]) \
		-> (
				list[float],
				Union[CollectivePostOutputsS2PoolDict, CollectivePostOutputsS2BilateralDict]
		):
	"""
	Iterative overarching algorithm for the post-delivery timeframe
	:param backpack: data for running the two-stage MILP
	:param pricing_func: market mechanism function to be applied
	:param optimization_func: optimization function to be applied
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:param kwargs: necessary flags or numeric parameters that are required by the passed func
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	# START THE LOOP
	logger.info('Starting loop...')

	# Initialize required data for obtaining the initial offers
	l_market_buy = backpack['l_market_buy']
	l_market_sell = backpack['l_market_sell']
	meters = backpack['meters'].copy()
	for meter_name, meter_data in meters.items():
		meter_data['e_met'] = [c - g for c, g in zip(meter_data['e_c'], meter_data['e_g'])]
	nr_sessions = time_intervals(backpack['horizon'], backpack['delta_t'])
	end = False

	# Auxiliary function for logging
	dynamic_size = lambda val: int(3 - len(str(int(val))))

	milp_results = None  # Initialize the results variable

	logger.info('################################################################')
	while True:
		# Build the current offers, order them and calculate the P2P price
		buys, sells = make_offers(meters, nr_sessions, l_market_buy, l_market_sell)

		# Calculate initial LEM prices
		logger.info(f'Calculating LEM prices for all sessions...')
		l_lem = [pricing_func(buys[t], sells[t], **kwargs) for t in range(nr_sessions)]

		# Validate the outputted LEM prices
		assert isinstance(l_lem, list)
		for price in l_lem:
			assert isinstance(price, Union[float, int])
		assert len(l_lem) == nr_sessions

		# Break after computing the final prices
		if end:
			break

		# Print the initial prices computed
		str_l_lem = [' ' * dynamic_size(x) + f"{x:.2f}" for x in l_lem]
		logger.info(f'/// Starting P2P prices: {"|".join(str_l_lem)}')

		# Update the LEM prices in the input data for the optimization procedure
		backpack['l_lem'] = l_lem

		# Run the optimization algorithm
		logger.info(f'Solving MILP...')
		milp_results = optimization_func(backpack, for_testing, solver)

		# Retrieve the new objective function value from the collective optimization,
		# that is associated with the REC total cost of operation
		of2 = milp_results[0]['obj_value']
		logger.info(f'--- O.F. value: ({round(of2, 3)})')

		# Retrieve the new e_met and update "meters" structure
		for meter_name, meter_data in milp_results[0]['e_cmet'].items():
			meters[meter_name]['e_met'] = meter_data

		# Signal the end of the iteration
		end = True

	# Calculate final LEM prices
	str_l_lem = [' ' * dynamic_size(x) + f"{x:.2f}" for x in l_lem]
	logger.info(f'/// Final P2P prices:    {"|".join(str_l_lem)}')

	# When a stopping criterion is met, return the computed prices
	logger.success(f'Stopped algorithm.')

	return l_lem, milp_results


def loop_post_pool_mmr(backpack: LoopPostBackpackS2PoolDict,
                       for_testing=False,
                       pruned=True,
                       divider=0.5,
					   solver='CBC') \
		-> (
				list[float],
				CollectivePostOutputsS2PoolDict
		):
	"""
	Function to compute the LEM prices' array through the application of the two-stage MILP,
	under a pool market structure, and the MMR mechanism.
	Since this function is specific for the post-delivery timeframe, the scheduled net loads of each member,
	found after running the two-stage MILP algorithm need only to be computed once.
	With those optimal scheduled offers, the LEM prices can be computed for each market session in the defined horizon.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param divider: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 0.5, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and between 0.0 and 1.0
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	assert 0.0 <= divider <= 1.0, 'Please provide a divider value between 0.0 and 1.0.'
	pricing_func = compute_pruned_mmr if pruned else compute_mmr
	opt_func = run_post_two_stage_collective_pool_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_highway(backpack,
	                       pricing_func,
	                       opt_func,
	                       for_testing,
	                       divider=divider,
						   solver=valid_solver)


def loop_post_pool_sdr(backpack: LoopPostBackpackS2PoolDict,
                       for_testing=False,
                       pruned=True,
                       compensation=0.0,
					   solver='CBC') \
		-> (
				list[float],
				CollectivePostOutputsS2PoolDict
		):
	"""
	Function to compute the LEM prices' array through the application of the two-stage MILP,
	under a pool market structure, and the SDR mechanism.
	Since this function is specific for the post-delivery timeframe, the scheduled net loads of each member,
	found after running the two-stage MILP algorithm need only to be computed once.
	With those optimal scheduled offers, the LEM prices can be computed for each market session in the defined horizon.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	assert 0.0 <= compensation <= 1.0, 'Please provide a compensation value between 0.0 and 1.0.'
	pricing_func = compute_pruned_sdr if pruned else compute_sdr
	opt_func = run_post_two_stage_collective_pool_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_highway(backpack,
	                       pricing_func,
	                       opt_func,
	                       for_testing,
	                       compensation=compensation,
						   solver=valid_solver)


def loop_post_pool_crossing_value(backpack: LoopPostBackpackS2PoolDict,
                                  for_testing=False,
                                  small_increment=0.0,
								  solver='CBC') \
		-> (
				list[float],
				CollectivePostOutputsS2PoolDict
		):
	"""
	Function to compute the LEM prices' array through the application of the two-stage MILP,
	under a pool market structure, and the clearing of a market pool with the buying and selling resulting offers.
	Since this function is specific for the post-delivery timeframe, the scheduled net loads of each member,
	found after running the two-stage MILP algorithm need only to be computed once.
	With those optimal scheduled offers, the LEM prices can be computed for each market session in the defined horizon.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param small_increment: float to add to buy offers' value and subtract from sell offers' value
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	pricing_func = compute_crossing_value
	opt_func = run_post_two_stage_collective_pool_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_highway(backpack,
	                       pricing_func,
	                       opt_func,
	                       for_testing,
	                       small_increment=small_increment,
						   solver=valid_solver)


def loop_post_bilateral_mmr(backpack: LoopPostBackpackS2BilateralDict,
                            for_testing=False,
                            pruned=True,
                            divider=0.5,
							solver='CBC') \
		-> (
				list[float],
				CollectivePostOutputsS2BilateralDict
		):
	"""
	Function to compute the LEM prices' array through the application of the two-stage MILP,
	under a p2p market structure, based on bilateral contracts, and the MMR mechanism.
	Since this function is specific for the post-delivery timeframe, the scheduled net loads of each member,
	found after running the two-stage MILP algorithm need only to be computed once.
	With those optimal scheduled offers, the LEM prices can be computed for each market session in the defined horizon.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param divider: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 0.5, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and between 0.0 and 1.0
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	assert 0.0 <= divider <= 1.0, 'Please provide a divider value between 0.0 and 1.0.'
	pricing_func = compute_pruned_mmr if pruned else compute_mmr
	opt_func = run_post_two_stage_collective_bilateral_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_highway(backpack,
	                       pricing_func,
	                       opt_func,
	                       for_testing,
	                       divider=divider,
						   solver=valid_solver)


def loop_post_bilateral_sdr(backpack: LoopPostBackpackS2BilateralDict,
                            for_testing=False,
                            pruned=True,
                            compensation=0.0,
							solver='CBC') \
		-> (
				list[float],
				CollectivePostOutputsS2BilateralDict
		):
	"""
	Function to compute the LEM prices' array through the application of the two-stage MILP,
	under a p2p market structure, based on bilateral contracts, and the SDR mechanism.
	Since this function is specific for the post-delivery timeframe, the scheduled net loads of each member,
	found after running the two-stage MILP algorithm need only to be computed once.
	With those optimal scheduled offers, the LEM prices can be computed for each market session in the defined horizon.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param pruned: if True, consider only offers that would be cleared on a market pool
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	assert 0.0 <= compensation <= 1.0, 'Please provide a compensation value between 0.0 and 1.0.'
	pricing_func = compute_pruned_sdr if pruned else compute_sdr
	opt_func = run_post_two_stage_collective_bilateral_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_highway(backpack,
	                       pricing_func,
	                       opt_func,
	                       for_testing,
	                       compensation=compensation,
						   solver=valid_solver)


def loop_post_bilateral_crossing_value(backpack: LoopPostBackpackS2BilateralDict,
                                       for_testing=False,
                                       small_increment=0.0,
									   solver='CBC') \
		-> (
				list[float],
				CollectivePostOutputsS2BilateralDict
		):
	"""
	Function to compute the LEM prices' array through the application of the two-stage MILP,
	under a p2p market structure, based on bilateral contracts, and the clearing of a market pool with
	the buying and selling resulting offers.
	Since this function is specific for the post-delivery timeframe, the scheduled net loads of each member,
	found after running the two-stage MILP algorithm need only to be computed once.
	With those optimal scheduled offers, the LEM prices can be computed for each market session in the defined horizon.
	The function requires the provision of several forecasts, parameters and other data which are thoroughly described
	below, under the parameter "backpack". Arrays with time-varying data such as consumption/generation forecasts and
	opportunity costs must comply with the expected length defined by the MILP's horizon and step
	(e.g., for a 24h horizon, and a step of 15 minutes or 0.25 hours, the length of the arrays must be 96).
	:param backpack: {
		'meters' : structure with information relative to each Meter / community member
		{
			#meter_id: {
				'e_c': an array with the forecasted Btm total energy consumption, in kWh
				'e_g': an array with the forecasted Btm total energy generation, in kWh
				'l_buy': an array with the opportunity costs for buying energy from the retailer
				'l_sell': an array with the opportunity costs for selling energy to the retailer
				'max_p': float with the maximum admissible power at the connection with the grid, in kW
					(e.g., can be the contracted power)
			}
		}
		'delta_t': a float or int with the optimization time step to be considered, in hours
		'horizon' a float or int with the horizon of the optimization (typically 24h), in hours
		'l_extra': a float representing a fictitious value penalizing overstepping "max_p", in €/kWh
		'l_grid': an array with the applicable tariffs for self-consumed energy, in €/kWh
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
	:param for_testing: when testing set to True, since parallelization of first stage does not work
	:param small_increment: float to add to buy offers' value and subtract from sell offers' value
	:param solver: one of "CBC", CPLEX" (other string reverts to "CBC"; if "CPLEX" is not available, reverts to "CBC")
	:return: tuple with:
		- array of float with the LEM prices computed;
			the order of the values in the array follows the same order of the provided data
		- full MILP outputs' structure of the solution
	"""
	pricing_func = compute_crossing_value
	opt_func = run_post_two_stage_collective_bilateral_milp

	# Validate the solver used
	if solver == 'CPLEX' and IS_CPLEX_AVAILABLE:
		valid_solver = 'CPLEX'
	else:
		valid_solver = 'CBC'
	logger.info(f'Solver: {valid_solver}')

	return _common_highway(backpack,
	                       pricing_func,
	                       opt_func,
	                       for_testing,
	                       small_increment=small_increment,
						   solver=valid_solver)
