INPUTS_S1 = {
	'btm_storage': {
		'Storage#1': {
			'degradation_cost': 0.01,
			'e_bn': 1.0,
			'eff_bc': 1.0,
			'eff_bd': 1.0,
			'init_e': 0.0,
			'p_max': 1.0,
			'soc_max': 100.0,
			'soc_min': 0.0
		}
	},
	'delta_t': 1.0,
	'e_c': [0.0, 0.5, 0.0],
	'e_g': [0.9, 0.0, 0.0],
	'horizon': 3.0,
	'id': 'Meter#1',
	'l_buy': [1.0, 2.0, 0.0],
	'l_extra': 10,
	'l_market_buy': [2.0, 2.0, 0.0],
	'l_market_sell': [0.0, 0.0, 1.0],
	'l_sell': [0.0, 0.0, 0.0],
	'max_p': 5.0
}

OUTPUTS_S1 = {
	'c_ind': -0.391,
	'c_ind_without_deg': -0.4,
	'c_ind_without_deg_and_p_extra': -0.4,
	'c_ind_without_p_extra': -0.391,
	'deg_cost': 0.009,
	'delta_bc': {'Storage#1': [1.0, 0.0, 0.0]},
	'delta_sup': [0.0, 0.0, 0.0],
	'e_bat': {'Storage#1': [0.9, 0.4, 0.0]},
	'e_bc': {'Storage#1': [0.9, 0.0, 0.0]},
	'e_bd': {'Storage#1': [0.0, 0.5, 0.4]},
	'e_cmet': [0.0, 0.0, -0.4],
	'e_sup_market': [0.0, 0.0, 0.0],
	'e_sup_retail': [0.0, 0.0, 0.0],
	'e_sur_market': [0.0, 0.0, 0.4],
	'e_sur_retail': [0.0, 0.0, 0.0],
	'meter_id': 'Meter#1',
	'milp_status': 'Optimal',
	'obj_value': -0.391,
	'p_extra': [0.0, 0.0, 0.0],
	'p_extra_cost': 0,
	'soc_bat': {'Storage#1': [90.0, 40.0, 0.0]}
}
