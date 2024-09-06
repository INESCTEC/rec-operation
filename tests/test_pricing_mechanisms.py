import rec_op_lem_prices.pricing_mechanisms.structures.examples as eg
import inspect

from rec_op_lem_prices.pricing_mechanisms.module.PricingMechanisms import (
	compute_crossing_value,
	compute_mmr,
	compute_pruned_mmr,
	compute_pruned_sdr,
	compute_sdr,
	do_offers_cross,
	get_accepted_offers,
	stop_criterion
)


def test_compute_mmr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -600, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 15}]
	sell_offers_cross = [{'origin': 4, 'amount': -500, 'value': 0},
	                     {'origin': 5, 'amount': -600, 'value': 10},
	                     {'origin': 6, 'amount': -500, 'value': 50}]

	no_buys_l_p2p = compute_mmr([], sell_offers)
	assert no_buys_l_p2p == 0  # assert that the minimum sell offer value is returned when there are no buying offers

	no_sells_l_p2p = compute_mmr(buy_offers, [])
	assert no_sells_l_p2p == 45  # assert that maximum buy offer value is returned when there are no selling offers

	no_offers_l_p2p = compute_mmr([], [])
	assert no_offers_l_p2p == 0  # assert that 0 is returned when no offers are made

	l_p2p = compute_mmr(buy_offers, sell_offers)
	assert l_p2p == 25.0  # assert the mmr is returned when buying and selling offers are made

	l_p2p = compute_mmr(buy_offers, sell_offers, divisor=3)
	assert round(l_p2p, 2) == 16.67  # assert the imr is returned when buying and selling offers are made

	cross_l_p2p = compute_mmr(buy_offers, sell_offers_cross)
	assert cross_l_p2p == 10.0  # assert the pool's cross value is return when offers cross


def test_compute_pruned_mmr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -600, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 15}]
	sell_offers_cross = [{'origin': 4, 'amount': -500, 'value': 0},
	                     {'origin': 5, 'amount': -600, 'value': 10},
	                     {'origin': 6, 'amount': -500, 'value': 50}]

	no_buys_l_p2p = compute_pruned_mmr([], sell_offers)
	assert no_buys_l_p2p == 0  # assert that the minimum sell offer value is returned when there are no buying offers

	no_sells_l_p2p = compute_pruned_mmr(buy_offers, [])
	assert no_sells_l_p2p == 0  # assert that maximum buy offer value is returned when there are no selling offers

	no_offers_l_p2p = compute_pruned_mmr([], [])
	assert no_offers_l_p2p == 0  # assert that 0 is returned when no offers are made

	l_p2p = compute_pruned_mmr(buy_offers, sell_offers)
	assert l_p2p == 25.0  # assert the mmr is returned when buying and selling offers are made

	l_p2p = compute_mmr(buy_offers, sell_offers, divisor=3)
	assert round(l_p2p, 2) == 16.67  # assert the imr is returned when buying and selling offers are made

	cross_l_p2p = compute_pruned_mmr(buy_offers, sell_offers_cross)
	assert cross_l_p2p == 22.5  # assert the pool's cross value is return when offers cross


def test_compute_pruned_sdr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -400, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 15}]
	sell_offers_cross = [{'origin': 4, 'amount': -500, 'value': 0},
	                     {'origin': 5, 'amount': -500, 'value': 10},
	                     {'origin': 6, 'amount': -500, 'value': 50}]
	excess_sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	                      {'origin': 5, 'amount': -500, 'value': 10},
	                      {'origin': 6, 'amount': -1000, 'value': 15}]
	deficit_sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	                       {'origin': 5, 'amount': -500, 'value': 10},
	                       {'origin': 6, 'amount': -250, 'value': 15}]

	no_buys_l_p2p = compute_pruned_sdr([], sell_offers, 0)
	assert no_buys_l_p2p == 0  # assert that the minimum sell offer value is returned when there are no buying offers

	no_sells_l_p2p = compute_pruned_sdr(buy_offers, [], 0)
	assert no_sells_l_p2p == 0  # assert that maximum buy offer value is returned when there are no selling offers

	no_offers_l_p2p = compute_pruned_sdr([], [], 0)
	assert no_offers_l_p2p == 0  # assert that 0 is returned when no offers are made

	l_p2p = compute_pruned_sdr(buy_offers, sell_offers, 0)
	assert round(l_p2p, 3) == 15.594  # assert the sdr is returned when buying and selling offers are made

	cross_l_p2p = compute_pruned_sdr(buy_offers, sell_offers_cross)
	assert cross_l_p2p == 10.0  # assert the pool's cross value is return when offers cross

	l_p2p_comp = compute_pruned_sdr(buy_offers, sell_offers, 0.5)
	assert round(l_p2p_comp, 3) == 25.485  # assert the sdrc is returned when buying and selling offers are made

	l_p2p_extra_sell = compute_pruned_sdr(buy_offers, excess_sell_offers, 0)
	assert l_p2p_extra_sell == 15.0  # assert the correct sdr is returned when sell offers _extra_buyexceed buy offers

	l_p2p_extra_buy = compute_pruned_sdr(buy_offers, deficit_sell_offers, 0)
	assert round(l_p2p_extra_buy, 3) == 16.579  # assert the correct sdr is returned when buy offers exceed sell offers


def test_compute_sdr():
	buy_offers = [{'origin': 1, 'amount': 500, 'value': 45},
	              {'origin': 2, 'amount': 500, 'value': 40},
	              {'origin': 3, 'amount': 500, 'value': 35}]
	sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	               {'origin': 5, 'amount': -400, 'value': 10},
	               {'origin': 6, 'amount': -500, 'value': 15}]
	sell_offers_cross = [{'origin': 4, 'amount': -500, 'value': 0},
	                     {'origin': 5, 'amount': -500, 'value': 10},
	                     {'origin': 6, 'amount': -500, 'value': 50}]
	excess_sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	                      {'origin': 5, 'amount': -500, 'value': 10},
	                      {'origin': 6, 'amount': -1000, 'value': 15}]
	deficit_sell_offers = [{'origin': 4, 'amount': -500, 'value': 0},
	                       {'origin': 5, 'amount': -500, 'value': 10},
	                       {'origin': 6, 'amount': -250, 'value': 15}]

	no_buys_l_p2p = compute_sdr([], sell_offers, 0)
	assert no_buys_l_p2p == 0  # assert that the minimum sell offer value is returned when there are no buying offers

	no_sells_l_p2p = compute_sdr(buy_offers, [], 0)
	assert no_sells_l_p2p == 45  # assert that maximum buy offer value is returned when there are no selling offers

	no_offers_l_p2p = compute_sdr([], [], 0)
	assert no_offers_l_p2p == 0  # assert that 0 is returned when no offers are made

	l_p2p = compute_sdr(buy_offers, sell_offers, 0)
	assert round(l_p2p, 3) == 15.594  # assert the sdr is returned when buying and selling offers are made

	cross_l_p2p = compute_sdr(buy_offers, sell_offers_cross)
	assert cross_l_p2p == 10.0  # assert the pool's cross value is return when offers cross

	l_p2p_comp = compute_sdr(buy_offers, sell_offers, 0.5)
	assert round(l_p2p_comp, 3) == 25.485  # assert the sdrc is returned when buying and selling offers are made

	l_p2p_extra_sell = compute_sdr(buy_offers, excess_sell_offers, 0)
	assert l_p2p_extra_sell == 15.0  # assert the correct sdr is returned when sell offers _extra_buyexceed buy offers

	l_p2p_extra_buy = compute_sdr(buy_offers, deficit_sell_offers, 0)
	assert round(l_p2p_extra_buy, 3) == 16.579  # assert the correct sdr is returned when buy offers exceed sell offers


def test_do_offers_cross():
	expected_l_p2p = {
		'Example01': True,
		'Example01a': True,
		'Example01b': True,
		'Example02': True,
		'Example02a': True,
		'Example02b': True,
		'Example03': False,
		'Example04': True,
		'Example05': False,
		'Example06': False,
		'Example07': True,
		'Example08': True
	}

	_classes = inspect.getmembers(eg, inspect.isclass)
	examples = [example_class for _, example_class in _classes]
	for example in examples:
		buy_offers_ = example.buy_offers
		sell_offers_ = example.sell_offers

		cross = do_offers_cross(buy_offers_, sell_offers_)
		# assert that the right values are computed
		assert cross == expected_l_p2p.get(example.__name__)


def test_get_accepted_offers():
	expected_lengths = {
		'Example01': (3, 3),
		'Example01a': (3, 3),
		'Example01b': (3, 3),
		'Example02': (3, 3),
		'Example02a': (3, 3),
		'Example02b': (3, 3),
		'Example03': (2, 3),
		'Example04': (2, 3),
		'Example05': (2, 2),
		'Example06': (2, 2),
		'Example07': (3, 2),
		'Example08': (3, 2)
	}

	_classes = inspect.getmembers(eg, inspect.isclass)
	examples = [example_class for _, example_class in _classes]
	for example in examples:
		buy_offers_ = example.buy_offers
		sell_offers_ = example.sell_offers

		accepted_buys, accepted_sells = get_accepted_offers(buy_offers_, sell_offers_)
		nr_buys = len(accepted_buys)
		nr_sells = len(accepted_sells)
		# assert that the right values are computed
		assert (nr_buys, nr_sells) == expected_lengths.get(example.__name__)


def test_compute_crossing_value():
	expected_l_p2p = {
		'Example01': 20,
		'Example01a': 20,
		'Example01b': 20,
		'Example02': 20,
		'Example02a': 20,
		'Example02b': 20,
		'Example03': 35,
		'Example04': 35,
		'Example05': 10,
		'Example06': 10,
		'Example07': 10,
		'Example08': 10
	}

	_classes = inspect.getmembers(eg, inspect.isclass)
	examples = [example_class for _, example_class in _classes]
	for example in examples:
		buy_offers_ = example.buy_offers
		sell_offers_ = example.sell_offers

		l_p2p = compute_crossing_value(buy_offers_, sell_offers_, small_increment=0)

		# from rec_op_lem_prices.pricing_mechanisms.module.PricingMechanisms import _plot_pool
		# _plot_pool(buy_offers_, sell_offers_, l_p2p, example.__name__)

		# assert that the right values are computed
		assert l_p2p == expected_l_p2p.get(example.__name__)


def test_stop_criterion():
	old_prices = [0.1, 0.2, 0.3, 0.4, 0.5]
	continue_new_prices = [0.1, 0.2, 0.3, 0.4, 0.7]
	stop_new_prices = [0.1, 0.2, 0.3, 0.4, 0.5000000001]

	stop, criterion = stop_criterion(old_prices, continue_new_prices)
	assert (stop, round(criterion, 3)) == (False, 0.200)

	stop, criterion = stop_criterion(old_prices, stop_new_prices)
	assert (stop, round(criterion, 3)) == (True, 0.000)


if __name__ == '__main__':
	test_compute_mmr()
	test_compute_pruned_mmr()
	test_compute_pruned_sdr()
	test_compute_sdr()
	test_do_offers_cross()
	test_get_accepted_offers()
	test_compute_crossing_value()
	test_stop_criterion()
