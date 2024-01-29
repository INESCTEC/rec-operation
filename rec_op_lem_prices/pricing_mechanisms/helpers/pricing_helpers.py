from rec_op_lem_prices.custom_types.pricing_mechanims_types import OffersList
from rec_op_lem_prices.custom_types.pricing_mechanisms_helpers_types import MetersDict
from loguru import logger
from typing import Union


def make_offers(meters: MetersDict,
                nr_sessions: int,
                l_market_buy: list[float],
                l_market_sell: list[float]) -> tuple[list[OffersList], list[OffersList]]:
	"""
	Helper function to create bidding offers based on REC members' forecasted or
	historical net loads and opportunity costs for buying or selling energy to the grid.
	For each market session, each member or Meter can make a single offer, which will be
	provided in the following format:
	{'origin': str, 'amount': float, 'value': float}
	where the amount is given in kWh, value in €/kWh and origin is an identification id,
	unique to each member / Meter.
	:param meters: {
		#meter_id: {
			'e_met': an array with the forecasted Btm net consumption (positive = consuming, negative = injecting),
				in kWh
			'l_buy': an array with the opportunity costs for buying energy from the retailer
			'l_sell': an array with the opportunity costs for selling energy to the retailer
		}
	}
	:param nr_sessions: number of market sessions (i.e., size of all data arrays)
	:param l_market_buy: an array with market-indexed buying tariffs in €/kWh
	:param l_market_sell: an array with market-indexed selling tariffs in €/kWh
	:return: tuple with a list of lists of buying offers and a list of lists of selling offers;
		the outer lists represent each market sessions and will have a length equal to "nr_sessions";
		the inner lists, one per market session, represent the offers made for that session
	"""
	logger.debug('Organizing buying and selling offers...')

	# Validate that all arrays have the same size as the total number of market sessions
	message = lambda l: f'{l} length does not correspond to total number of market sessions'
	assert nr_sessions == len(l_market_buy), message('"l_market_buy"')
	assert nr_sessions == len(l_market_sell), message('"l_market_sell"')
	for meter_nae, meter_data in meters.items():
		assert nr_sessions == len(meter_data['e_met']), message(f'"{meter_nae}[e_met]"')
		assert nr_sessions == len(meter_data['l_buy']), message(f'"{meter_nae}[buy]"')
		assert nr_sessions == len(meter_data['l_sell']), message(f'"{meter_nae}[sell]"')

	# Create final lists of buying and selling offers per market session
	buys = [[] for _ in range(nr_sessions)]
	sells = [[] for _ in range(nr_sessions)]

	# Fill the offer lists iterating over each Meter / member
	# The value of each buying and selling offer will be the most profitable for the Meter / member between
	# the market-indexed tariffs and the opportunity costs with the retailer
	for meter_nae, meter_data in meters.items():
		for t in range(nr_sessions):
			e_met = meter_data['e_met'][t]
			if e_met > 0:
				buy_value = min(meter_data['l_buy'][t], l_market_buy[t])
				buys[t].append({
					'origin': meter_nae,
					'amount': e_met,
					'value': buy_value
				})
			elif e_met < 0:
				sell_value = max(meter_data['l_sell'][t], l_market_sell[t])
				sells[t].append({
					'origin': meter_nae,
					'amount': abs(e_met),
					'value': sell_value
				})

	logger.debug('Organizing buying and selling offers... DONE!')

	return buys, sells
