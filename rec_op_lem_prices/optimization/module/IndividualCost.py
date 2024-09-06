"""
Class for calculating the individual Meter cost for post-delivery optimization.
"""
import numpy as np

from rec_op_lem_prices.custom_types.individual_cost_types import (
	BackpackIndCostDict,
	OutputsIndCostDict
)
from loguru import logger


def calculate_individual_cost(backpack: BackpackIndCostDict) -> OutputsIndCostDict:
	"""
	Used to compute the individual cost with energy for a Meter, for a given horizon.
	This function should be used to compute the	individual costs per Meter used as restrictions
	for the post-delivery collective optimization that will	define the optimal transactions within a REC,
	equivalently to how Stage 1 MILP is used on the pre-delivery timeframe.
	Note that no information about controllable assets (namely batteries) is used since this is only meant
	to be used in the post-delivery timeframe, and their operation will not be scheduled since it already took
	place.
	The temporal granularity of the provided arrays needs to be explicit, and is passed through the "delta_t"
	parameter. On the other hand, all arrays must have the same length (i.e., the same operation horizon).
	:param backpack: dictionary with all post-delivery data needed
	:return: dictionary comprised of an array with the calculated extra power flows at the Meter (absolute values)
	and the individual cost with energy for the Meter
	"""

	# Parameters
	_delta_t = backpack.get('delta_t')  # interval settlement duration [h]
	_l_buy = np.array(backpack.get('l_buy'))  # supply energy tariff [€/kWh]
	_l_sell = np.array(backpack.get('l_sell'))  # feed in energy tariff [€/kWh]
	_l_market_buy = np.array(backpack.get('l_market_buy'))  # market-indexed buying tariff [€/kWh]
	_l_market_sell = np.array(backpack.get('l_market_sell'))  # market-indexed selling tariff [€/kWh]
	_p_meter_max = backpack.get('max_p')  # maximum power flow desired at the Meter [kW]
	_l_extra = backpack.get('l_extra')  # (fictitious) very high cost of violating p_meter_max
	_e_met = backpack.get('e_met')  # net consumption (positive = imported; negative = exported) [kWh]
	meter_id = backpack.get('id')  # identification of the Meter for which te MILP will run

	# Assert that all arrays provided have the same length (i.e., operation horizon)
	baseline_length = len(_l_buy)
	assert len(_l_sell) == baseline_length, 'length of "l_sell" does not match the length of "l_buy"'
	assert len(_l_market_buy) == baseline_length, 'length of "l_market_buy" does not match the length of "l_buy"'
	assert len(_l_market_sell) == baseline_length, 'length of "l_market_sell" does not match the length of "l_buy"'
	assert len(_e_met) == baseline_length, 'length of "e_met" does not match the length of "l_buy"'

	logger.debug(f'-- calculating the individual cost for Meter id: {meter_id}...')

	# Decide how to optimally distribute the net load (when equal, defaults to retailer)
	e_sup_retail = np.zeros(baseline_length)  # energy effectively bought from the supplier [kWh]
	e_sur_retail = np.zeros(baseline_length)  # energy effectively sold to the supplier [kWh]
	e_sup_market = np.zeros(baseline_length)  # energy effectively bought at an OMIE-indexed price [kWh]
	e_sur_market = np.zeros(baseline_length)  # energy effectively sold at an OMIE-indexed price [kWh]
	for pos, net_load in enumerate(_e_met):
		if net_load >= 0:
			if _l_buy[pos] > _l_market_buy[pos]:
				e_sup_market[pos] = net_load
			else:
				e_sup_retail[pos] = net_load
		else:
			if _l_sell[pos] >= _l_market_sell[pos]:
				e_sur_retail[pos] = -net_load
			else:
				e_sur_market[pos] = -net_load

	# Calculate the absolute of the extra power flow at the Meter
	energy_flows = e_sup_retail + e_sup_market - e_sur_retail - e_sur_market
	abs_energy_flows = abs(energy_flows)
	abs_power_flows = abs_energy_flows / _delta_t
	raw_p_extra = abs_power_flows - _p_meter_max
	p_extra_array = np.maximum(raw_p_extra, 0)
	p_extra = p_extra_array.tolist()

	# Calculate the cost with energy
	c_ind_array = (e_sup_retail * _l_buy - e_sur_retail * _l_sell
				   + e_sup_market * _l_market_buy - e_sur_market * _l_market_sell
				   + p_extra_array * _l_extra)
	c_ind = c_ind_array.sum()

	logger.debug(f'-- calculating the individual cost for Meter id: {meter_id}... DONE!')

	return {
		'c_ind': c_ind,
		'meter_id': meter_id,
		'e_sup_market': list(e_sup_market),
		'e_sup_retail': list(e_sup_retail),
		'e_sur_market': list(e_sur_market),
		'e_sur_retail': list(e_sur_retail),
		'p_extra': p_extra
	}
