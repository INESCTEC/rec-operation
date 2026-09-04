INPUTS_S2_POOL_HVAC = {
	'delta_t': 1,
    'horizon': 4,
	'l_extra': 10,
	'l_grid': [0.01] * 4,
	'l_lem': [0.2, 0.2, 0.2, 0.2],
    'l_market_buy': [1.5, 1.5, 1.5, 1.5],
    'l_market_sell': [0.14, 0.14, 0.14, 0.14],
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
			'c_ind': 1.1,
            'e_c': [0.0000, 0.1211, 0.2421, 0.3632],
            'e_g': [0.9000, 0.6821, 0.4642, 0.2463],
            'l_buy': [0.16, 0.16, 0.16, 0.16],
            'l_sell': [0.04, 0.04, 0.04, 0.04],
            'max_p': 40.0,
            'hvac': {
                'HVAC#1': {
                    'type': 'inverter',
                    'mu': 0.1,
                    'psi': 3,
                    'temp_min': 18.0,
                    'temp_max': 23.0,
                    'init_temp': 22,
                    'hvac_capacity': 2,
                    't_out': [22.0000, 22.0000, 30.0000, 30.0000],
                    'thermal_resist': 4,
                    'thermal_cap': 0.3
                },
                'HVAC#2': {
                  'type': 'state',
                   'mu': 0.1,
                   'psi': 4,
                   'temp_min': 18.0,
                   'temp_max': 24.0,
                  'init_temp': 22,
                   'hvac_capacity': 2,
                   't_out': [22.0000, 22.0000, 22.0000, 22.0000],
                   'thermal_resist': 5,
                   'thermal_cap': 0.2
                }
            }
        },
		'Meter#2': {
            'btm_storage': None,
            'c_ind': -0.69,
            'e_c': [0.0000, 0.1211, 0.2421, 0.3632],
            'e_g': [0.9000, 0.6821, 0.4642, 0.2463],
            'l_buy': [0.16, 0.16, 0.16, 0.16],
            'l_sell': [0.04, 0.04, 0.04, 0.04],
            'max_p': 40.0,
            'hvac': {
                'HVAC#1': {
                    'type': 'inverter',
                    'mu': 0.1,
                    'psi': 6,
                    'temp_min': 18.0,
                    'temp_max': 23.0,
                    'init_temp': 22,
                    'hvac_capacity': 2,
                    't_out': [25.0000, 26.0000, 27.0000, 28.0000],
                    'thermal_resist': 3,
                    'thermal_cap': 0.5
                }
            }
        },
    },
    'second_stage': False,
    'strict_pos_coeffs': True,
    'sum_one_coeffs': False
}
OUTPUTS_S2_POOL_HVAC = {'obj_value': -0.32302900000000007, 'milp_status': 'Optimal', 'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_sur_market': {'Meter#1': [0.8883, 0.161, 0.0, 0.0], 'Meter#2': [0.9, 0.161, 0.2221, 0.0]}, 'delta_sup': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.1169]}, 'e_sale_pool': {'Meter#1': [0.0, 0.0, 0.0, 0.1169], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_cmet': {'Meter#1': [-0.8883, -0.161, 0.0, -0.1169], 'Meter#2': [-0.9, -0.161, -0.2221, 0.1169]}, 'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.1169]}, 'e_consumed': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.1169]}, 'e_alc': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.1169]}, 'delta_slc': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 1.0]}, 'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'delta_alc': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'p_extra': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_bat': {'Meter#1': {'Storage#1': [0.0117, 0.0117, 0.2338, 0.0]}, 'Meter#2': {}}, 'soc_bat': {'Meter#1': {'Storage#1': [1.17, 1.17, 23.38, 0.0]}, 'Meter#2': {}}, 'e_bc': {'Meter#1': {'Storage#1': [0.0117, 0.0, 0.2221, 0.0]}, 'Meter#2': {}}, 'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.0, 0.0, 0.2338]}, 'Meter#2': {}}, 'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 1.0, 0.0]}, 'Meter#2': {}}, 'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'hvac_power': {'Meter#1': {'HVAC#1': [0.0, 0.4, 0.0, 0.0], 'HVAC#2': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'HVAC#1': [0.0, 0.4, 0.0, 0.0]}}, 'hvac_temp': {'Meter#1': {'HVAC#1': [22.0, 20.8, 21.72, 22.548], 'HVAC#2': [22.0, 22.0, 22.0, 22.0]}, 'Meter#2': {'HVAC#1': [22.0, 20.0, 20.7, 21.43]}}, 'hvac_cost_comfort': {'Meter#1': {'HVAC#1': [0.0, 0.0, 0.0, 0.0], 'HVAC#2': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'HVAC#1': [0.0, 0.0, 0.0, 0.0]}}, 'c_ind2pool': {'Meter#1': -0.168, 'Meter#2': -0.155}, 'c_ind2pool_without_deg': {'Meter#1': -0.17, 'Meter#2': -0.155}, 'c_ind2pool_without_deg_and_p_extra': {'Meter#1': -0.17, 'Meter#2': -0.155}, 'c_ind2pool_without_p_extra': {'Meter#1': -0.168, 'Meter#2': -0.155}, 'deg_cost2pool': {'Meter#1': 0.0023380000000000002, 'Meter#2': 0}, 'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0}, 'dual_prices': [0.14, 0.14, 0.14, 0.15]}
