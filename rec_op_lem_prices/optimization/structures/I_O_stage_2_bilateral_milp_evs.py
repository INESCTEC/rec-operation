INPUTS_S2_BILATERAL_EVS = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': {
		'Meter#1': {
			'Meter#2': [0.01, 0.01, 0.01]
		},
		'Meter#2': {
			'Meter#1': [0.01, 0.01, 0.01]
		}
	},
	'l_lem': [1.5, 1.5, 1.5],
	'l_market_buy': [3.0, 3.0, 3.0],
	'l_market_sell': [0.1, 0.1, 0.1],
	'meters': {
		'Meter#1': {
			'btm_storage': {
				'Storage#1': {
					'degradation_cost': 0.01,
					'e_bn': 1.0,
					'eff_bc': 1.0,
					'eff_bd': 1.0,
					'init_e': 0.0,
					'p_max': 1.0,
					'soc_max': 100.0,
					'soc_min': 0.0}
			},
				'btm_evs': {'EV#1': {
				'trip_ev': [0, 0, 0],
				'min_energy_storage_ev': 0,
				'battery_capacity_ev': 1.0,
				'eff_bc_ev': 0.99,
				'eff_bd_ev': 0.99,
				'init_e_ev': 0.9,
				'pmax_c_ev': 0.1,
				'pmax_d_ev': 0.1,
				'bin_ev': [1, 1, 1] #1 when plugged
					}
			},
			'c_ind': 0.0,
			'e_c': [0.0, 0.5, 0.0],
			'e_g': [0.9, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.9],
			'max_p': 5.0
		},
		'Meter#2': {
			'btm_storage': None,
			'c_ind': 0.600,
			'e_c': [0.1, 0.1, 0.1],
			'e_g': [0.0, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.0],
			'max_p': 5.0
		}
	},
	'second_stage': False,  # these inputs are used for testing the second stage of the two-stage approach
	'strict_pos_coeffs': True,
	'sum_one_coeffs': False}

OUTPUTS_S2_BILATERAL_EVS = {
	'obj_value': -0.345,
	 'milp_status': 'Optimal',
	 'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.397], 'Meter#2': [0.0, 0.0, 0.0]},
	 'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]}, 'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
	 'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.1, 0.1, 0.1]}, 'Meter#2': {'Meter#1': [0.0, 0.0, 0.0]}},
	 'e_cmet': {'Meter#1': [-0.1, -0.1, -0.497], 'Meter#2': [0.1, 0.1, 0.1]},
	 'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]}, 'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
	 'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	 'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	 'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'e_bat': {'Meter#1': {'Storage#1': [0.899, 0.398, 0.0]}, 'Meter#2': {}},
	 'soc_bat': {'Meter#1': {'Storage#1': [89.9, 39.8, 0.0]}, 'Meter#2': {}},
	 'e_bc': {'Meter#1': {'Storage#1': [0.899, 0.0, 0.0]}, 'Meter#2': {}},
	 'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.501, 0.398]}, 'Meter#2': {}},
	 'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
	 'ev_stored': {'Meter#1': {'EV#1': [0.8, 0.7, 0.6]}, 'Meter#2': {}},
	 'p_ev_charge': {'Meter#1': {'EV#1': [0.0, 0.0, 0.0]}, 'Meter#2': {}},
	 'p_ev_discharge': {'Meter#1': {'EV#1': [0.099, 0.099, 0.099]}, 'Meter#2': {}},
	 'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	 'c_ind2bilateral': {'Meter#1': -0.798, 'Meter#2': 0.453},
	 'c_ind2bilateral_without_deg': {'Meter#1': -0.807, 'Meter#2': 0.453},
	 'c_ind2bilateral_without_deg_and_p_extra': {'Meter#1': -0.807, 'Meter#2': 0.453},
	 'c_ind2bilateral_without_p_extra': {'Meter#1': -0.798, 'Meter#2': 0.453},
	 'deg_cost2bilateral': {'Meter#1': 0.00899, 'Meter#2': 0},
	 'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0}

}