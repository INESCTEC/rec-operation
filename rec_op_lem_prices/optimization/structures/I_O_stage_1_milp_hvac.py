
INPUTS_S1_HVAC = {
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
				'hvac': {
					'HVAC#1': {
						'type': 'inverter',
						'mu': 0.1,
						'psi': 3,
						'temp_min': 22,
						'temp_max': 24.0,
						'init_temp': 20,
						'hvac_capacity': 2,
						't_out': [22, 23, 24, 24],
						'thermal_resist': 4,
						'thermal_cap': 0.3
					},
					'HVAC#2': {
					    'type': 'state',
					    'mu': 0.1,
					    'psi': 4,
					    'temp_min': 22,
					    'temp_max': 24.0,
					    'init_temp': 22,
					    'hvac_capacity': 2,
					    't_out': [22, 23, 24, 24],
					    'thermal_resist': 6,
					    'thermal_cap': 0.2
				}
	},'delta_t': 1,
	'horizon': 4,
	'l_extra': 10,
	'l_market_buy': [1.5, 1.5, 1.5, 1.5],
	'l_market_sell': [0.1, 0.1, 0.1, 0.1],
            'e_c': [0.157, 0.282411, 0.407821, 0.533232],
            'e_g': [0.0, 0.0, 0.0, 0.0],
            'l_buy': [0.16, 0.16, 0.16, 0.16],
            'l_sell': [0.04, 0.04, 0.04, 0.04],
            'max_p': 40.0,
	'id': 'Meter#1'

	}
OUTPUTS_S1_HVAC = {'meter_id': 'Meter#1', 'obj_value': 0.34887424, 'milp_status': 'Optimal', 'e_sup_retail': [0.157, 1.082411, 0.407821, 0.533232], 'e_sur_retail': [0.0, 0.0, 0.0, 0.0], 'e_sup_market': [0.0, 0.0, 0.0, 0.0], 'e_sur_market': [0.0, 0.0, 0.0, 0.0], 'delta_sup': [1.0, 1.0, 1.0, 1.0], 'e_cmet': [0.157, 1.082411, 0.407821, 0.533232], 'p_extra': [0.0, 0.0, 0.0, 0.0], 'e_g': [0.0, 0.0, 0.0, 0.0], 'e_bat': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'soc_bat': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'e_bc': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'e_bd': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'delta_bc': {'Storage#1': [1.0, 0.0, 0.0, 0.0]}, 'hvac_temp': {'HVAC#1': [20.0, 22.7, 22.83, 22.947], 'HVAC#2': [22.0, 22.565402, 23.376526, 23.729039]}, 'hvac_power': {'HVAC#1': [0.0, 0.8, 0.0, 0.0], 'HVAC#2': [0.0, 0.0, 0.0, 0.0]}, 'cost_comfort': {'HVAC#1': [2.0, 0.0, 0.0, 0.0], 'HVAC#2': [0.0, 0.0, 0.0, 0.0]}, 'deg_cost': 0.0, 'p_extra_cost': 0.0, 'c_ind': 0.34887424, 'c_ind_without_deg': 0.34887424, 'c_ind_without_p_extra': 0.34887424, 'c_ind_without_deg_and_p_extra': 0.34887424}

