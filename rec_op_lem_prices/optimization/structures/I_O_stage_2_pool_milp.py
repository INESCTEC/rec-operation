INPUTS_S2_POOL = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_lem': [1.1, 1.1, 1.1],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
			'c_ind': -0.391,
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
	'second_stage': True,  # these inputs are used for testing the second stage of the two-stage approach
	'strict_pos_coeffs': True,
	'sum_one_coeffs': False
}

OUTPUTS_S2_POOL = {
	'c_ind2pool': {'Meter#1': -0.422, 'Meter#2': 0.333},
	'c_ind2pool_without_deg': {'Meter#1': -0.430, 'Meter#2': 0.333},
	'c_ind2pool_without_deg_and_p_extra': {'Meter#1': -0.430,	'Meter#2': 0.333},
	'c_ind2pool_without_p_extra': {'Meter#1': -0.422,	'Meter#2': 0.333},
	'deg_cost2pool': {'Meter#1': 0.008, 'Meter#2': 0},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0],	'Meter#2': [0.0, 0.0, 0.0]},
	'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'dual_prices': [0.99, 1.0, 1.0],
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_bat': {'Meter#1': {'Storage#1': [0.8, 0.2, 0.0]}, 'Meter#2': {}},
	'e_bc': {'Meter#1': {'Storage#1': [0.8, 0.0, 0.0]}, 'Meter#2': {}},
	'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.6, 0.2]}, 'Meter#2': {}},
	'e_cmet': {'Meter#1': [-0.1, -0.1, -0.2], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_sale_pool': {'Meter#1': [0.1, 0.1, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_market': {'Meter#1': [0.0, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': -0.089,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0},
	'soc_bat': {'Meter#1': {'Storage#1': [80.0, 20.0, 0.0]}, 'Meter#2': {}}
}

INPUTS_S2_DUAL = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.0, 0.0, 0.0],
	'l_lem': [0.0, 0.0, 0.0],
	'l_market_buy': [10.0, 10.0, 10.0],
	'l_market_sell': [0.0, 0.0, 0.0],
	'meters': {
		'Meter#1': {
			'btm_storage': None,
			'c_ind': 0.0,
			'e_c': [0.0, 0.5, 0.0],
			'e_g': [0.9, 0.0, 0.1],
			'l_buy': [2.0, 2.0, 2.0],
			'l_sell': [1.0, 1.0, 1.0],
			'max_p': 5.0
		},
		'Meter#2': {
			'btm_storage': None,
			'c_ind': 0.0,
			'e_c': [0.1, 0.1, 0.2],
			'e_g': [0.0, 0.0, 0.0],
			'l_buy': [1.9, 1.9, 1.9],
			'l_sell': [1.1, 1.1, 1.1],
			'max_p': 5.0
		}
	},
	'second_stage': False,   # these inputs are used for testing the individual collective MILP with duals
	'strict_pos_coeffs': True,
	'sum_one_coeffs': False
}

OUTPUTS_S2_DUAL = {
	'c_ind2pool': {'Meter#1': 1.0, 'Meter#2': -0.5},
	'c_ind2pool_without_deg': {'Meter#1': 1.0, 'Meter#2': -0.5},
	'c_ind2pool_without_deg_and_p_extra': {'Meter#1': 1.0, 'Meter#2': -0.5},
	'c_ind2pool_without_p_extra': {'Meter#1': 1.0, 'Meter#2': -0.5},
	'deg_cost2pool': {'Meter#1': 0, 'Meter#2': 0},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_bc': {'Meter#1': {}, 'Meter#2': {}},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 1.0, 0.0], 'Meter#2': [1.0, 1.0, 1.0]},
	'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_sup': {'Meter#1': [1.0, 1.0, 1.0], 'Meter#2': [0.0, 1.0, 1.0]},
	'dual_prices': [1.1, 2.0, 1.9],
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.9, 0.0, 0.1]},
	'e_bat': {'Meter#1': {}, 'Meter#2': {}},
	'e_bc': {'Meter#1': {}, 'Meter#2': {}},
	'e_bd': {'Meter#1': {}, 'Meter#2': {}},
	'e_cmet': {'Meter#1': [-0.9, 0.5, -0.1], 'Meter#2': [0.1, 0.1, 0.2]},
	'e_consumed': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.2]},
	'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.9, 0.0, 0.1]},
	'e_sale_pool': {'Meter#1': [0.9, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.9, 0.0, 0.1]},
	'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.0, 0.1, 0.1]},
	'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.8, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': 0.500,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0},
	'soc_bat': {'Meter#1': {}, 'Meter#2': {}}
}

SINGLE_PRE_INPUTS_S2_POOL = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_lem': [1.1, 1.1, 1.1],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
	'sum_one_coeffs': False
}

SINGLE_PRE_OUTPUTS_S2_POOL = {
	'c_ind2pool': {'Meter#1': -0.422, 'Meter#2': 0.333},
	'c_ind2pool_without_deg': {'Meter#1': -0.43, 'Meter#2': 0.333},
	'c_ind2pool_without_deg_and_p_extra': {'Meter#1': -0.43, 'Meter#2': 0.333},
	'c_ind2pool_without_p_extra': {'Meter#1': -0.422, 'Meter#2': 0.333},
	'deg_cost2pool': {'Meter#1': 0.008, 'Meter#2': 0},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [1.0, 1.0, 1.0]},
	'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'dual_prices': [0.99, 1.0, 1.0],
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_bat': {'Meter#1': {'Storage#1': [0.8, 0.2, 0.0]}, 'Meter#2': {}},
	'e_bc': {'Meter#1': {'Storage#1': [0.8, 0.0, 0.0]}, 'Meter#2': {}},
	'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.6, 0.2]}, 'Meter#2': {}},
	'e_cmet': {'Meter#1': [-0.1, -0.1, -0.2], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_sale_pool': {'Meter#1': [0.1, 0.1, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_market': {'Meter#1': [0.0, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': -0.089,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0},
	'soc_bat': {'Meter#1': {'Storage#1': [80.0, 20.0, 0.0]}, 'Meter#2': {}}
}

COLLECTIVE_PRE_INPUTS_S2_POOL = SINGLE_PRE_INPUTS_S2_POOL.copy()

COLLECTIVE_PRE_OUTPUTS_S2_POOL = (
	{
		'c_ind2pool': {'Meter#1': -0.422, 'Meter#2': 0.332},
		'c_ind2pool_without_deg': {'Meter#1': -0.43, 'Meter#2': 0.332},
		'c_ind2pool_without_deg_and_p_extra': {'Meter#1': -0.43, 'Meter#2': 0.332},
		'c_ind2pool_without_p_extra': {'Meter#1': -0.422, 'Meter#2': 0.332},
		'deg_cost2pool': {'Meter#1': 0.008, 'Meter#2': 0},
		'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_bc': {'Meter#1': {'Storage#1': [1.0, 0.0, 0.0]}, 'Meter#2': {}},
		'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_coeff': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_slc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_sup': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'dual_prices': [0.99, 1.0, 1.0],
		'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_bat': {'Meter#1': {'Storage#1': [0.8, 0.2, 0.0]}, 'Meter#2': {}},
		'e_bc': {'Meter#1': {'Storage#1': [0.8, 0.0, 0.0]}, 'Meter#2': {}},
		'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.6, 0.2]}, 'Meter#2': {}},
		'e_cmet': {'Meter#1': [-0.1, -0.1, -0.2], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_consumed': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_sale_pool': {'Meter#1': [0.1, 0.1, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_sup_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sur_market': {'Meter#1': [0.0, 0.0, 0.1], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sur_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'milp_status': 'Optimal',
		'obj_value': -0.089,
		'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0},
		'soc_bat': {'Meter#1': {'Storage#1': [80.0, 20.0, 0.0]}, 'Meter#2': {}}
	},
	[
		{
			'c_ind': -0.391,
			'c_ind_without_deg': -0.4,
			'c_ind_without_deg_and_p_extra': -0.4,
			'c_ind_without_p_extra': -0.391,
			'meter_id': 'Meter#1',
			'deg_cost': 0.009000000000000001,
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
			'milp_status': 'Optimal',
			'obj_value': -0.391,
			'p_extra': [0.0, 0.0, 0.0],
			'p_extra_cost': 0.0,
			'soc_bat': {'Storage#1': [90.0, 40.0, 0.0]}
		},
		{
			'c_ind': 0.6000000000000001,
			'c_ind_without_deg': 0.6000000000000001,
			'c_ind_without_deg_and_p_extra': 0.6000000000000001,
			'c_ind_without_p_extra': 0.6000000000000001,
			'meter_id': 'Meter#2',
			'deg_cost': 0,
			'delta_bc': {},
			'delta_sup': [1.0, 1.0, 1.0],
			'e_bat': {},
			'e_bc': {},
			'e_bd': {},
			'e_cmet': [0.1, 0.1, 0.1],
			'e_sup_market': [0.1, 0.1, 0.1],
			'e_sup_retail': [0.0, 0.0, 0.0],
			'e_sur_market': [0.0, 0.0, 0.0],
			'e_sur_retail': [0.0, 0.0, 0.0],
			'milp_status': 'Optimal',
			'obj_value': 0.6000000000000001,
			'p_extra': [0.0, 0.0, 0.0],
			'p_extra_cost': 0.0,
			'soc_bat': {}
		}
	]
)

SINGLE_POST_INPUTS_S2_POOL = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_lem': [1.1, 1.1, 1.1],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
	'sum_one_coeffs': False
}

SINGLE_POST_OUTPUTS_S2_POOL = {
	'c_ind2pool': {'Meter#1': 0.89, 'Meter#2': 0.511},
	'c_ind2pool_without_p_extra': {'Meter#1': 0.89, 'Meter#2': 0.511},
	'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'delta_coeff': {'Meter#1': [0.0, 1.0, 0.0], 'Meter#2': [0.0, 1.0, 1.0]},
	'delta_slc': {'Meter#1': [1.0, 0.0, 1.0], 'Meter#2': [1.0, 0.0, 0.0]},
	'delta_sup': {'Meter#1': [0.0, 1.0, 1.0], 'Meter#2': [0.0, 1.0, 1.0]},
	'dual_prices': [0.0, 2.0, 2.0],
	'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
	'e_cmet': {'Meter#1': [-0.9, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_consumed': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
	'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
	'e_sale_pool': {'Meter#1': [0.1, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
	'e_sup_market': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.1, 0.1]},
	'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'e_sur_retail': {'Meter#1': [0.8, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'milp_status': 'Optimal',
	'obj_value': 1.401,
	'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
	'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0}
}

COLLECTIVE_POST_INPUTS_S2_POOL = SINGLE_POST_INPUTS_S2_POOL.copy()

COLLECTIVE_POST_OUTPUTS_S2_POOL = (
	{
		'c_ind2pool': {'Meter#1': 0.89, 'Meter#2': 0.511},
		'c_ind2pool_without_p_extra': {'Meter#1': 0.89, 'Meter#2': 0.511},
		'delta_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'delta_coeff': {'Meter#1': [0.0, 1.0, 0.0], 'Meter#2': [0.0, 1.0, 1.0]},
		'delta_slc': {'Meter#1': [1.0, 0.0, 1.0], 'Meter#2': [1.0, 0.0, 0.0]},
		'delta_sup': {'Meter#1': [0.0, 1.0, 1.0], 'Meter#2': [0.0, 1.0, 1.0]},
		'dual_prices': [0.0, 2.0, 2.0],
		'e_alc': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
		'e_cmet': {'Meter#1': [-0.9, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_consumed': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.1, 0.1, 0.1]},
		'e_pur_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
		'e_sale_pool': {'Meter#1': [0.1, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_slc_pool': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.1, 0.0, 0.0]},
		'e_sup_market': {'Meter#1': [0.0, 0.5, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.1, 0.1]},
		'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'e_sur_retail': {'Meter#1': [0.8, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'milp_status': 'Optimal',
		'obj_value': 1.401,
		'p_extra': {'Meter#1': [0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0]},
		'p_extra_cost2pool': {'Meter#1': 0.0, 'Meter#2': 0.0}
	},
	[
		{
			'c_ind': 1.0,
			'meter_id': 'Meter#1',
			'e_sup_market': [0.0, 0.0, 0.0],
			'e_sup_retail': [0.0, 0.5, 0.0],
			'e_sur_market': [0.0, 0.0, 0.0],
			'e_sur_retail': [0.9, 0.0, 0.0],
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

DUAL_PRE_PRICES_INPUTS = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
	'sum_one_coeffs': False
}

DUAL_PRE_PRICES_OUTPUTS = [0.99, 1.0, 1.0]

DUAL_POST_PRICES_INPUTS = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
	'sum_one_coeffs': False
}

DUAL_POST_PRICES_OUTPUTS = [0.0, 2.0, 2.0]

LOOP_PRE_INPUTS_S2_POOL = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
	'sum_one_coeffs': False
}

LOOP_PRE_OUTPUTS_S2_POOL_MMR = ([1.0, 1.0, 1.5], 0.0, 3)

LOOP_PRE_OUTPUTS_S2_POOL_SDR = ([0.0, 0.0, 1.0], 0.0, 3)

LOOP_PRE_OUTPUTS_S2_POOL_CV = ([0.0, 2.0, 2.0], 0.0, 4)

LOOP_POST_INPUTS_S2_POOL = {
	'delta_t': 1.0,
	'horizon': 3.0,
	'l_extra': 10,
	'l_grid': [0.01, 0.01, 0.01],
	'l_market_buy': [2.0, 2.0, 2.0],
	'l_market_sell': [0.0, 0.0, 1.0],
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
	'sum_one_coeffs': False
}

LOOP_POST_OUTPUTS_S2_POOL_MMR = [1.0, 0.0, 0.0]

LOOP_POST_OUTPUTS_S2_POOL_SDR = [0.0, 0.0, 0.0]

LOOP_POST_OUTPUTS_S2_POOL_CV = [0.0, 2.0, 2.0]
