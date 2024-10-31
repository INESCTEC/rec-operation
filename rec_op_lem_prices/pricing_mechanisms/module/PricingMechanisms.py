import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rec_op_lem_prices.custom_types.pricing_mechanims_types import (
	OffersList,
	PricesList
)
from copy import deepcopy
from loguru import logger


def _cumsum_offers(buys: OffersList, sells: OffersList, small_increment=0.0) -> tuple[OffersList, OffersList]:
	"""
	Function that returns buy and sell offers' lists as accumulated sums
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
	:param small_increment: a small increment that can be added to sell offers and subtracted to buy offers
	:return: screened buy offers' list and sell offers' list
	"""
	logger.trace(' - converting offers into accumulated sums...')

	# Check if both offers' lists are empty and if so, return them as the empty lists that they are
	if (len(buys) == 0) and (len(sells) == 0):
		return buys, sells

	# Abs values for sell offers
	for sell in sells:
		sell['amount'] = abs(sell['amount'])

	# Sort offers by value (note: deepcopy needed to preserve original lists)
	sellers = deepcopy(sells)
	buyers = deepcopy(buys)
	sellers = sorted(sellers, key=lambda x: x['value'] + small_increment)
	buyers = sorted(buyers, key=lambda x: x['value'] - small_increment, reverse=True)

	# Turn amounts into accumulated sums
	for i, v in enumerate(sellers):
		if i > 0:
			sellers[i]['amount'] += sellers[i - 1]['amount']
	for i, v in enumerate(buyers):
		if i > 0:
			buyers[i]['amount'] += buyers[i - 1]['amount']

	logger.trace(' - converting offers into accumulated sums... DONE!')
	return buyers, sellers


def _parsing(offers: OffersList):
	"""
	Auxiliary function for sorting and aggregating buying or selling offers, based on their prices
	:param offers: list of offers
	:return: list of aggregated offers
	"""
	# Include first step
	offers.insert(0, {'origin': None, 'amount': 0, 'value': offers[0]['value']})
	agg_offers = pd.DataFrame(offers)

	# Aggregate amounts
	agg_offers['amount'] = agg_offers['amount'].cumsum()

	# Remove first column 'origin'
	agg_offers = agg_offers[['amount', 'value']]

	return agg_offers


def _plot_pool(buy_offers: OffersList, sell_offers: OffersList, l_p2p: float, example_name: str):
	"""
	Plot the crossing of buy offers and sell offers as step plot
	:param buy_offers: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sell_offers: same structure but for selling offers
	:param l_p2p: calculated price for transactions, in €/kWh, given the buying and selling offers
	:param example_name: title for the plot
	"""
	agg_sellers = _parsing(sell_offers)
	agg_buyers = _parsing(buy_offers)

	# Calculate max total amount to sell or buy to plot target_value
	target_amount = [0, max(agg_sellers['amount'].iloc[-1], agg_buyers['amount'].iloc[-1])]
	target_value = [l_p2p, l_p2p]

	plt.step(x=agg_sellers['amount'], y=agg_sellers['value'], label='sell offers')
	plt.step(x=agg_buyers['amount'], y=agg_buyers['value'], label='buy_offers')
	plt.step(x=target_amount, y=target_value, linestyle='--', label='p2p price')
	plt.xlabel('kWh')
	plt.ylabel('€/kWh')
	plt.legend()
	plt.title(f'{example_name}')
	plt.show()

	return


def compute_mmr(buys: OffersList, sells: OffersList, divisor=2.0) -> float:
	"""
	Function to compute the mid-market rate (MMR);
	If the divisor is set to a value different from 2, the function is broadened and should be considered as the more
	general intermediary-market rate (IMR);
	If any of the selling offers has a higher value than any of the buying offers,
	the pool crossing value is returned instead
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: same structure but for selling offers
	:param divisor: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 2.0, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and > 0.0
	:return: calculated price for transactions
	"""
	logger.debug('Computing pool price through MMR...')

	buy_offers = pd.DataFrame(buys)
	sell_offers = pd.DataFrame(sells)

	# If only buyers return most costly offer
	if sell_offers.empty and not buy_offers.empty:
		logger.debug('There are no selling offers.')
		return buy_offers['value'].max()

	# If only sellers return less costly offer
	elif buy_offers.empty and not sell_offers.empty:
		logger.debug('There are no buying offers.')
		return sell_offers['value'].min()

	# If no buyers nor sellers, return 0
	elif buy_offers.empty or sell_offers.empty:
		logger.debug('There are no buying nor selling offers.')
		return 0

	# Calculate max l_buy and max l_sell per timestep among consuming and exporting peers, respectively
	min_buy = buy_offers['value'].min()
	max_sell = sell_offers['value'].max()

	# If the minimum buy price is smaller than the maximum sell price,
	# return the crossing value instead
	if min_buy < max_sell:
		logger.warning('No market price can be established through MMR '
		               'since the minimum buy offer has a smaller price '
		               'than the maximum sell offer. '
		               'Returning the pools\' cross value.')
		return compute_crossing_value(buys, sells)

	result = (min_buy + max_sell) / divisor

	logger.debug(f'Computing pool price through MMR... DONE!')
	return result


def compute_pruned_mmr(buys: OffersList, sells: OffersList, divisor=2.0) -> float:
	"""
	Function to compute the mid-market rate (MMR)
	using only aggregated offers that are accepted on a community market pool;
	If the divisor is set to a value different from 2, the function is broadened and should be considered as the more
	general intermediary-market rate (IMR);
	If any of the selling offers has a higher value than any of the buying offers,
	the pool crossing value is returned instead
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: same structure but for selling offers
	:param divisor: the value establishing how close the LEM price is positioned from the least valuable buying offer
	and the most valuable selling offer; By default, the value is 2.0, making the price equidistant from both offers;
	Higher values skew the price towards the selling offers and smaller values towards the buying offers.
	Note: must be non-negative and > 0.0
	:return: calculated price for transactions, in €/kWh
	"""
	logger.debug('(Opted for pruned MMR approach)')
	pruned_buys, pruned_sells = get_accepted_offers(buys, sells)
	return compute_mmr(pruned_buys, pruned_sells, divisor)


def compute_pruned_sdr(buys: OffersList, sells: OffersList, compensation=0.0) -> float:
	"""
	Function to compute the supply and demand ratio (SDR), compensated (SDRC) or not,
	using only aggregated offers that are accepted on a community market pool;
	If any of the selling offers has a higher value than any of the buying offers,
	the pool crossing value is returned instead
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: same structure but for selling offers
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:return: calculated price for transactions, in €/kWh
	"""
	logger.debug('(Opted for pruned SDR approach)')
	pruned_buys, pruned_sells = get_accepted_offers(buys, sells)
	return compute_sdr(pruned_buys, pruned_sells, compensation)


def compute_sdr(buys: OffersList, sells: OffersList, compensation=0.0) -> float:
	"""
	Function to compute the supply and demand ratio (SDR), compensated (SDRC) or not;
	If any of the selling offers has a higher value than any of the buying offers,
	the pool crossing value is returned instead
	:param buys: list of buying offers, each with the structure {'origin': str, 'amount': float, 'value': float};
	amount is given in kWh, value in €/kWh and origin is an identification id, unique to each offer
	:param sells: same structure but for selling offers
	:param compensation: float between 0 and 1 that establishes the relative compensation
	:return: calculated price for transactions, in €/kWh
	"""
	logger.debug('Computing pool price through SDR...')

	assert 0 <= compensation <= 1, "Please provide a value for compensation that is between 0.0 and 1.0"
	buy_offers = pd.DataFrame(buys)
	sell_offers = pd.DataFrame(sells)

	# -- if only buyers return most costly offer
	if sell_offers.empty and not buy_offers.empty:
		logger.debug('There are no selling offers.')
		return buy_offers['value'].max()

	# -- if only sellers return less costly offer
	elif buy_offers.empty and not sell_offers.empty:
		logger.debug('There are no buying offers.')
		return sell_offers['value'].min()

	# -- if no buyers nor sellers, return 0
	elif buy_offers.empty and sell_offers.empty:
		logger.debug('There are no buying nor selling offers.')
		return 0

	# -- else, make sure that sell offers' amount is a positive value
	# (e.g., for compute_crossing_value function it is not)
	else:
		sell_offers['amount'] = abs(sell_offers['amount'])

	# Calculate total consumption and total exported amounts
	e_q = sell_offers['amount'].sum()
	d_q = buy_offers['amount'].sum()

	# Calculate min l_buy and max l_sell per timestep among consuming and exporting peers, respectively
	min_buy = buy_offers['value'].min()
	max_sell = sell_offers['value'].max()

	# If the minimum buy price is smaller than the maximum sell price,
	# return the crossing value instead
	if min_buy < max_sell:
		logger.warning('No market price can be established through SDR '
		               'since the minimum buy offer has a smaller price '
		               'than the maximum sell offer. '
		               'Returning the pools\' cross value.')
		return compute_crossing_value(buys, sells)

	# Compute l_compensation (if simple SDR, compensation = 0, so l_compensation = 0)
	l_compensation = (min_buy - max_sell) * compensation

	# Compute SDR values
	sdr = e_q / d_q
	if sdr == np.inf:
		result = 0
	elif sdr >= 1:
		result = max_sell + l_compensation / sdr
	elif 0 <= sdr < 1:
		result = (min_buy * (max_sell + l_compensation)) / \
		         ((min_buy - max_sell - l_compensation) * sdr + max_sell + l_compensation)
	else:
		raise ValueError('A negative SDR was computed. Please contact the developers.')

	logger.debug(f'Computing pool price through SDR... DONE!')
	return result


def do_offers_cross(buys: OffersList, sells: OffersList) -> bool:
	"""
	Function to check if buy and sell offers cross on a market pool,
	i.e., if any of the sell offers' value is higher than any of the buy offers' value.
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
	:return: boolean indicating the crossing or not
	"""
	logger.debug('Checking if offers cross...')

	# Check if both offers' lists are empty and if so, return 0 as the price
	if (len(buys) == 0) and (len(sells) == 0):
		return False

	# Turn amounts into accumulated sums
	buyers, sellers = _cumsum_offers(buys, sells)

	# Apply algorithm to find crossing value
	result = buyers[-1]['value'] < sellers[-1]['value']

	logger.debug('Checking if offers cross... DONE!')
	return result


def get_accepted_offers(buys: OffersList, sells: OffersList) -> tuple[OffersList, OffersList]:
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
	logger.debug('Pruning offers...')

	screened_buys = []
	screened_sells = []

	# Check if both offers' lists are empty and if so, return them as the empty lists that they are
	if (len(buys) == 0) and (len(sells) == 0):
		return screened_buys, screened_sells

	# Turn amounts into accumulated sums
	buyers, sellers = _cumsum_offers(buys, sells)

	# If there are only buyers or only sellers, there will be no accepted offers,
	# so empty lists must be returned
	if len(sellers) == 0 or len(buyers) == 0:
		return screened_buys, screened_sells

	# If there are sellers and buyers, screen which are the accepted offers
	s = 0
	b = 0
	last_rescued = 'BOTH'
	while (s < len(sellers)) and (b < len(buyers)):
		if sellers[s]['value'] > buyers[b]['value']:
			break
		elif buyers[b]['amount'] < sellers[s]['amount']:
			screened_buys.append(buys[b])
			b += 1
			last_rescued = 'BUY'
		elif sellers[s]['amount'] < buyers[b]['amount']:
			screened_sells.append(sells[s])
			s += 1
			last_rescued = 'SELL'
		else:
			screened_buys.append(buys[b])
			screened_sells.append(sells[s])
			b += 1
			s += 1
			last_rescued = 'BOTH'
	if last_rescued == 'BUY':
		screened_sells.append(sells[s])
	elif last_rescued == 'SELL':
		screened_buys.append(buys[b])

	logger.debug('Pruning offers... DONE!')
	return screened_buys, screened_sells


def compute_crossing_value(buys: OffersList, sells: OffersList, small_increment=0.001) -> float:
	"""
	Function to order the market offers and to calculate the crossing value.
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
	:param small_increment: a small increment can be added to sell offers and subtracted to buy offers to promote
		convergence of the overarching iterative algorithm
	:return: resulting price for the pool
	"""
	logger.debug('Computing the pool\'s crossing value...')

	# Check if both offers' lists are empty and if so, return 0 as the price
	if (len(buys) == 0) and (len(sells) == 0):
		return 0

	# Turn amounts into accumulated sums
	buyers, sellers = _cumsum_offers(buys, sells, small_increment)

	# Apply algorithm to find crossing value
	crossing_value = None

	# -- if only buyers return most costly offer
	if len(sellers) == 0 and len(buyers) > 0:
		crossing_value = buyers[0]['value']

	# -- if only sellers return less costly offer
	elif len(buyers) == 0 and len(sellers) > 0:
		crossing_value = sellers[0]['value']

	# -- if sellers and buyers, calculate pool
	else:
		last_sold_position = sellers[0]['value']
		s = 0
		b = 0
		while (s < len(sellers)) and (b < len(buyers)):
			if sellers[s]['value'] >= buyers[b]['value']:
				crossing_value = last_sold_position
				break
			else:
				last_sold_position = sellers[s]['value']
				if buyers[b]['amount'] > sellers[s]['amount']:
					crossing_value = buyers[b]['value']
					s += 1
				else:
					crossing_value = sellers[s]['value']
					b += 1

	logger.debug('Computing the pool\'s crossing value... DONE!')
	return crossing_value


def stop_criterion(old_prices: PricesList, new_prices: PricesList) -> tuple[bool, float]:
	"""
	Stopping criterion for the iterative algorithm that computes the P2P prices
	Version #1: check if the average difference between prices,
	for hours when at least one of them (old or new) is > 0,
	is smaller than 0.01 €/kWh
	:param old_prices: price vector from previous iteration of the overarching algorithm; prices are provided in €/kWh
	:param new_prices: price vector from current iteration of the overarching algorithm; prices are provided in €/kWh
	:return: boolean indicating if stopping criterion was met or not
	and the value of that stopping criterion (in this case the Euclidean distance between both input vectors)
	"""
	logger.debug('Evaluating the stopping criterion...')
	old_prices_ = np.array(old_prices)
	new_prices_ = np.array(new_prices)
	euclidean_distance = np.sqrt(np.sum(np.square(old_prices_ - new_prices_)))
	stop = euclidean_distance < 0.01

	logger.debug('Evaluating the stopping criterion... DONE!')
	return stop, euclidean_distance
