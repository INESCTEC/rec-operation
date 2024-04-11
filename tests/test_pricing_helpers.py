from rec_op_lem_prices.pricing_mechanisms.helpers.pricing_helpers import make_offers


def test_make_offers():
	meters = {
			'Meter#1': {
				'e_met': [-1.0, 1.0, 0.0, 1.0],
				'l_buy': [1.9, 1.9, 1.9, 1.5],
				'l_sell': [1.1, 1.1, 1.1, 1.2]
			},
			'Meter#2': {
				'e_met': [1.0, -1.0, 0.0, 1.0],
				'l_buy': [3.0, 3.0, 3.0, 1.4],
				'l_sell': [0.0, 0.0, 0.0, 1.3],
			}
		}
	l_market_buy = [2.0, 2.0, 2.0, 2.0]
	l_market_sell = [1.0, 1.0, 1.0, 1.0]
	nr_sessions = 4
	buys, sells = make_offers(meters, nr_sessions, l_market_buy, l_market_sell)
	assert buys == [
		[{'origin': 'Meter#2', 'amount': 1.0, 'value': 2.0}],
		[{'origin': 'Meter#1', 'amount': 1.0, 'value': 1.9}],
		[],
		[{'origin': 'Meter#1', 'amount': 1.0, 'value': 1.5},
		 {'origin': 'Meter#2', 'amount': 1.0, 'value': 1.4}],
	]
	assert sells == [
		[{'origin': 'Meter#1', 'amount': 1.0, 'value': 1.1}],
		[{'origin': 'Meter#2', 'amount': 1.0, 'value': 1.0}],
		[],
		[]
	]


if __name__ == '__main__':
	test_make_offers()
