INPUTS_S2_BILATERAL = {
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
	'total_share_coeffs': False
}

OUTPUTS_S2_BILATERAL = {
	'c_ind2bilateral': {'Meter#1': -0.532, 'Meter#2': 0.453},
	'c_ind2bilateral_without_deg': {'Meter#1': -0.54, 'Meter#2': 0.453},
	'c_ind2bilateral_without_deg_and_p_extra': {'Meter#1': -0.54, 'Meter#2': 0.453},
	'c_ind2bilateral_without_p_extra': {'Meter#1': -0.532, 'Meter#2': 0.453},
	'deg_cost2bilateral': {'Meter#1': 0.008, 'Meter#2': 0},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 1.0]},
	'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_bat': {'Meter#1': {'Storage#1': [0.8, 0.2, 0.0]}, 'Meter#2': {}},
	'e_bc': {'Meter#1': {'Storage#1': [0.8, 0.0, 0.0]}, 'Meter#2': {}},
	'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.6, 0.2]}, 'Meter#2': {}},
	'e_cmet': {'Meter#1': [-0.1, -0.1, -0.2], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
	                    'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
	'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.1, 0.1, 0.1]},
	                     'Meter#2': {'Meter#1': [0.0, 0.0, 0.0]}},
	'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
	                    'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
	'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': -0.079,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0},
	'soc_bat': {'Meter#1': {'Storage#1': [80.0, 20.0, 0.0]}, 'Meter#2': {}}
}

SINGLE_PRE_INPUTS_S2_BILATERAL = {
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
			'e_c': [0.0, 0.5, 0.0],
			'e_g': [0.9, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.9],
			'max_p': 5.0
		},
		'Meter#2': {
			'btm_storage': None,
			'e_c': [0.1, 0.1, 0.1],
			'e_g': [0.0, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.0],
			'max_p': 5.0
		}
	},
	'strict_pos_coeffs': True,
	'total_share_coeffs': False
}

SINGLE_PRE_OUTPUTS_S2_BILATERAL = {
	'c_ind2bilateral': {'Meter#1': -0.532, 'Meter#2': 0.453},
	'c_ind2bilateral_without_deg': {'Meter#1': -0.54, 'Meter#2': 0.453},
	'c_ind2bilateral_without_deg_and_p_extra': {'Meter#1': -0.54, 'Meter#2': 0.453},
	'c_ind2bilateral_without_p_extra': {'Meter#1': -0.532, 'Meter#2': 0.453},
	'deg_cost2bilateral': {'Meter#1': 0.008, 'Meter#2': 0},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 1.0]},
	'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_bat': {'Meter#1': {'Storage#1': [0.8, 0.2, 0.0]}, 'Meter#2': {}},
	'e_bc': {'Meter#1': {'Storage#1': [0.8, 0.0, 0.0]}, 'Meter#2': {}},
	'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.6, 0.2]}, 'Meter#2': {}},
	'e_cmet': {'Meter#1': [-0.1, -0.1, -0.2], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
	                    'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
	'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.1, 0.1, 0.1]},
	                     'Meter#2': {'Meter#1': [0.0, 0.0, 0.0]}},
	'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
	                    'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
	'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': -0.079,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0},
	'soc_bat': {'Meter#1': {'Storage#1': [80.0, 20.0, 0.0]}, 'Meter#2': {}}
}

COLLECTIVE_PRE_INPUTS_S2_BILATERAL = SINGLE_PRE_INPUTS_S2_BILATERAL.copy()

COLLECTIVE_PRE_OUTPUTS_S2_BILATERAL = (
	{
		'c_ind2bilateral': {'Meter#1': -0.532, 'Meter#2': 0.452},
		'c_ind2bilateral_without_deg': {'Meter#1': -0.54, 'Meter#2': 0.452},
		'c_ind2bilateral_without_deg_and_p_extra': {'Meter#1': -0.54, 'Meter#2': 0.452},
		'c_ind2bilateral_without_p_extra': {'Meter#1': -0.532, 'Meter#2': 0.452},
		'deg_cost2bilateral': {'Meter#1': 0.008, 'Meter#2': 0},
		'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
		'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 1.0]},
		'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_bat': {'Meter#1': {'Storage#1': [0.8, 0.2, 0.0]}, 'Meter#2': {}},
		'e_bc': {'Meter#1': {'Storage#1': [0.8, 0.0, 0.0]}, 'Meter#2': {}},
		'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.6, 0.2]}, 'Meter#2': {}},
		'e_cmet': {'Meter#1': [-0.1, -0.1, -0.2], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
		                    'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
		'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.1, 0.1, 0.1]},
		                     'Meter#2': {'Meter#1': [0.0, 0.0, 0.0]}},
		'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
		                    'Meter#2': {'Meter#1': [0.1, 0.1, 0.1]}},
		'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
		'milp_status': 'Optimal',
		'obj_value': -0.079,
		'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0},
		'soc_bat': {'Meter#1': {'Storage#1': [80.0, 20.0, 0.0]}, 'Meter#2': {}}},
	[
		{
			'c_ind': -0.351,
			'c_ind_without_deg': -0.360,
			'c_ind_without_deg_and_p_extra': -0.360,
			'c_ind_without_p_extra': -0.351,
			'meter_id': 'Meter#1',
			'deg_cost': 0.009,
			'delta_bc': {'Storage#1': [1.0, 0.0, 0.0]},
			'delta_sup': [0.0, 0.0, 0.0],
			'e_bat': {'Storage#1': [0.9, 0.4, 0.0]},
			'e_bc': {'Storage#1': [0.9, 0.0, 0.0]},
			'e_bd': {'Storage#1': [0.0, 0.5, 0.4]},
			'e_cmet': [0.0, 0.0, -0.4],
			'e_sup_market': [0.0, 0.0, 0.0],
			'e_sup_retail': [0.0, 0.0, 0.0],
			'e_sur_market': [0.0, 0.0, 0.0],
			'e_sur_retail': [0.0, 0.0, 0.4],
			'milp_status': 'Optimal',
			'obj_value': -0.351,
			'p_extra': [0.0, 0.0, 0.0],
			'p_extra_cost': 0.0,
			'soc_bat': {'Storage#1': [90.0, 40.0, 0.0]}
		},
		{
			'c_ind': 0.600,
			'c_ind_without_deg': 0.600,
			'c_ind_without_deg_and_p_extra': 0.600,
			'c_ind_without_p_extra': 0.600,
			'meter_id': 'Meter#2',
			'deg_cost': 0,
			'delta_bc': {},
			'delta_sup': [1.0, 1.0, 1.0],
			'e_bat': {},
			'e_bc': {},
			'e_bd': {},
			'e_cmet': [0.1, 0.1, 0.1],
			'e_sup_market': [0.0, 0.0, 0.0],
			'e_sup_retail': [0.1, 0.1, 0.1],
			'e_sur_market': [0.0, 0.0, 0.0],
			'e_sur_retail': [0.0, 0.0, 0.0],
			'milp_status': 'Optimal',
			'obj_value': 0.600,
			'p_extra': [0.0, 0.0, 0.0],
			'p_extra_cost': 0.0,
			'soc_bat': {}
		}
	]
)

SINGLE_POST_INPUTS_S2_BILATERAL = {
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
			'e_c': [0.0, 0.5, 0.0],
			'e_g': [0.9, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.9],
			'max_p': 5.0
		},
		'Meter#2': {
			'e_c': [0.1, 0.1, 0.1],
			'e_g': [0.0, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.0],
			'max_p': 5.0
		}
	},
	'strict_pos_coeffs': True,
	'total_share_coeffs': False
}

SINGLE_POST_OUTPUTS_S2_BILATERAL = {
	'c_ind2bilateral': {'Meter#1': 0.77, 'Meter#2': 0.551},
	'c_ind2bilateral_without_p_extra': {'Meter#1': 0.77, 'Meter#2': 0.551},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 1.0, 0.0], 'Meter#2': [1.0, 1.0, 1.0]},
	'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_sup': {'Meter#1': [0.0, 1.0, 1.0], 'Meter#2': [0.0, 1.0, 1.0]},
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
	'e_cmet': {'Meter#1': [-0.9, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_consumed': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
	                    'Meter#2': {'Meter#1': [0.1, 0.0, 0.0]}},
	'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.1, 0.0, 0.0]},
	                     'Meter#2': {'Meter#1': [0.0, 0.0, 0.0]}},
	'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
                        'Meter#2': {'Meter#1': [0.1, 0.0, 0.0]}},
	'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.0, 0.1, 0.1]},
	'e_sur_market': {'Meter#1': [0.8, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': 1.321,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0}
}

COLLECTIVE_POST_INPUTS_S2_BILATERAL = SINGLE_POST_INPUTS_S2_BILATERAL.copy()

COLLECTIVE_POST_OUTPUTS_S2_BILATERAL = (
	{
		'c_ind2bilateral': {'Meter#1': 0.77, 'Meter#2': 0.551},
		'c_ind2bilateral_without_p_extra': {'Meter#1': 0.77, 'Meter#2': 0.551},
		'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_coeff': {'Meter#1': [0.0, 1.0, 0.0], 'Meter#2': [1.0, 1.0, 1.0]},
		'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_sup': {'Meter#1': [0.0, 1.0, 1.0], 'Meter#2': [0.0, 1.0, 1.0]},
		'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
		'e_cmet': {'Meter#1': [-0.9, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_consumed': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
		                    'Meter#2': {'Meter#1': [0.1, 0.0, 0.0]}},
		'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.1, 0.0, 0.0]},
		                     'Meter#2': {'Meter#1': [0.0, 0.0, 0.0]}},
		'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0]},
		                    'Meter#2': {'Meter#1': [0.1, 0.0, 0.0]}},
		'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sup_retail': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.0, 0.1, 0.1]},
		'e_sur_market': {'Meter#1': [0.8, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'milp_status': 'Optimal',
		'obj_value': 1.321,
		'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0}
	},
	[
		{
			'c_ind': 0.91,
			'meter_id': 'Meter#1',
			'e_sup_market': [0.0, 0.0, 0.0],
			'e_sup_retail': [0.0, 0.5, 0.0],
			'e_sur_market': [0.9, 0.0, 0.0],
			'e_sur_retail': [0.0, 0.0, 0.0],
			'p_extra': [0.0, 0.0, 0.0]
		},
		{
			'c_ind': 0.6,
			'meter_id': 'Meter#2',
			'e_sup_market': [0.0, 0.0, 0.0],
			'e_sup_retail': [0.1, 0.1, 0.1],
			'e_sur_market': [0.0, 0.0, 0.0],
			'e_sur_retail': [0.0, 0.0, 0.0],
			'p_extra': [0.0, 0.0, 0.0]
		}
	]
)

LOOP_PRE_INPUTS_S2_BILATERAL = {
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
			'e_c': [0.0, 0.5, 0.0],
			'e_g': [0.9, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.9],
			'max_p': 5.0
		},
		'Meter#2': {
			'btm_storage': None,
			'e_c': [0.1, 0.1, 0.1],
			'e_g': [0.0, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.0],
			'max_p': 5.0
		}
	},
	'strict_pos_coeffs': True,
	'total_share_coeffs': False
}

LOOP_PRE_OUTPUTS_S2_BILATERAL_MMR = ([1.05, 1.05, 1.45], 0.0, 3)

LOOP_PRE_OUTPUTS_S2_BILATERAL_SDR = ([0.0, 0.0, 0.9], 0.0, 3)

LOOP_PRE_OUTPUTS_S2_BILATERAL_CV = ([0.1, 2.0, 2.0], 0.0, 4)

LOOP_POST_INPUTS_S2_BILATERAL = {
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
	'l_market_buy': [3.0, 3.0, 3.0],
	'l_market_sell': [0.1, 0.1, 0.1],
	'meters': {
		'Meter#1': {
			'e_c': [0.0, 0.5, 0.0],
			'e_g': [0.9, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.9],
			'max_p': 5.0
		},
		'Meter#2': {
			'e_c': [0.1, 0.1, 0.1],
			'e_g': [0.0, 0.0, 0.0],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [0.0, 0.0, 0.0],
			'max_p': 5.0
		}
	},
	'strict_pos_coeffs': True,
	'total_share_coeffs': False
}

LOOP_POST_OUTPUTS_S2_BILATERAL_MMR = [1.05, 0.0, 0.0]

LOOP_POST_OUTPUTS_S2_BILATERAL_SDR = [0.1, 0.0, 0.0]

LOOP_POST_OUTPUTS_S2_BILATERAL_CV = [0.1, 2.0, 2.0]
