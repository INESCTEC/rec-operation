INPUTS_S2_BILATERAL_HP = {
    'delta_t': 1,
    'horizon': 4,
    'l_extra': 10,
    'l_grid': {
    'Meter#1': {
        'Meter#2': [0.01] * 4,
    },
    'Meter#2': {
        'Meter#1': [0.01] * 4,
    }
	},
    'l_lem': [0.5] * 4,
    'l_market_buy': [0.1406, 0.1406, 0.1406, 0.1406],
    'l_market_sell': [0.0022, 0.0022, 0.0022, 0.0022],
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
                    'soc_min': 0.0
                }
            },
            'c_ind': -2.062,
            'e_c': [0.03925, 0.070603, 0.10195525, 0.133308],
            'e_g': [0.116382, 0.171867, 0.262206, 0.327495],
            'l_buy': [0.15] * 4,
            'l_sell': [0.04] * 4,
            'max_p': 40.0,
            'hp': {
                'HP#1': {
                    'type': 'inverter',  # or 'inverter'
                    'power_rated': 4.0,  # Rated power of HP [kW]
                    'capacity_tank': 500,  # Water tank capacity [kg]
                    'c_p': 4.18,  # Specific heat capacity of water [kJ/kg°C]

                    # Initial and desired temperatures
                    'temp_inlet': 15.0,  # Inlet water temp [°C]
                    'temp_desired': 55.0,  # Desired water temp [°C]
                    'temp_out_init': 50.0,  # Initial outlet temp [°C]
                    'temp_indoor_init': 18,  # Initial indoor temp [°C]
                    'temp_indoor_final': 22,  # Final indoor temp [°C]

                    # Comfort temperature bounds
                    'temp_indoor_min': 20.0,  # Min indoor temp [°C]
                    'temp_indoor_max': 24.0,  # Max indoor temp [°C]
                    'temp_out_min': 50.0,  # Min outlet temp [°C]
                    'temp_out_max': 70.0,  # Max outlet temp [°C]

                    # Building parameters
                    'u_value': 0.3,  # Building heat loss coefficient [kW/°C]
                    'thermal_resistance': 3,  # Building thermal resistance coefficient
                    'h_rad': 0.05,  # Convective heat transfer coeff of radiator [kW/m2°C]
                    'area_rad': 5.0,  # Radiator surface area [m²]

                    # External time-varying series
                    'mass_hw_demand': [0.0, 1 , 1, 2],
                    'mass_radiator': [50] * 4,
                    't_out': [14, 14, 14, 14],
                    }
                },
        },
        'Meter#2': {
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
            'c_ind': -2.221,
            'e_c': [0.15025, 0.13675, 0.12325, 0.10975],
            'e_g': [1.58179, 1.791474, 1.961116, 2.097664],
            'l_buy': [0.16] * 4,
            'l_sell': [0.04] * 4,
            'max_p': 40.0,
            'hp': {
                'HP#1': {
                    'type': 'inverter',  # or 'inverter'
                    'power_rated': 4.0,  # Rated power of HP [kW]
                    'capacity_tank': 500,  # Water tank capacity [kg]
                    'c_p': 4.18,  # Specific heat capacity of water [kJ/kg°C]

                    # Initial and desired temperatures
                    'temp_inlet': 15.0,  # Inlet water temp [°C]
                    'temp_desired': 55.0,  # Desired water temp [°C]
                    'temp_out_init': 50.0,  # Initial outlet temp [°C]
                    'temp_indoor_init': 18,  # Initial indoor temp [°C]
                    'temp_indoor_final': 22,  # Final indoor temp [°C]

                    # Comfort temperature bounds
                    'temp_indoor_min': 20.0,  # Min indoor temp [°C]
                    'temp_indoor_max': 24.0,  # Max indoor temp [°C]
                    'temp_out_min': 50.0,  # Min outlet temp [°C]
                    'temp_out_max': 70.0,  # Max outlet temp [°C]

                    # Building parameters
                    'u_value': 0.3,  # Building heat loss coefficient [kW/°C]
                    'thermal_resistance': 3,  # Building thermal resistance coefficient
                    'h_rad': 0.05,  # Convective heat transfer coeff of radiator [kW/m2°C]
                    'area_rad': 5.0,  # Radiator surface area [m²]

                    # External time-varying series
                    'mass_hw_demand': [0.0, 1, 1, 2],
                    'mass_radiator': [50] * 4,
                    't_out': [14, 14, 14, 14],
                }
            },
        }
    },
    'second_stage': False,
    'strict_pos_coeffs': True,
    'sum_one_coeffs': False,
    'total_share_coeffs': False
}

OUTPUTS_S2_BILATERAL_HP = {'obj_value': 0.451, 'milp_status': 'Optimal', 'e_sup_retail': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_sur_retail': {'Meter#1': [0.0, 0.054819556, 0.11380631, 0.10129811], 'Meter#2': [0.0, 0.043686738, 0.41711705, 0.52072061]}, 'e_sup_market': {'Meter#1': [2.4600455, 0.0, 0.0, 0.0], 'Meter#2': [1.1056375, 0.0, 0.0, 0.0]}, 'e_sur_market': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'delta_sup': {'Meter#1': [1.0, 0.0, 0.0, 0.0], 'Meter#2': [1.0, 0.0, 0.0, 0.0]}, 'e_pur_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Meter#1': [0.0, 0.0, 0.0, 0.0]}}, 'e_sale_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Meter#1': [0.0, 0.0, 0.0, 0.0]}}, 'e_cmet': {'Meter#1': [2.4600455, -0.054819556, -0.11380631, -0.10129811], 'Meter#2': [1.1056375, -0.043686738, -0.41711705, -0.52072061]}, 'e_slc_bilateral': {'Meter#1': {'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Meter#1': [0.0, 0.0, 0.0, 0.0]}}, 'e_consumed': {'Meter#1': [2.4600455, 0.0, 0.0, 0.0], 'Meter#2': [1.1056375, 0.0, 0.0, 0.0]}, 'e_alc': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'delta_slc': {'Meter#1': [0.0, 1.0, 0.0, 0.0], 'Meter#2': [0.0, 1.0, 0.0, 0.0]}, 'delta_cmet': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'delta_alc': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'p_extra': {'Meter#1': [0.0, 0.0, 0.0, 0.0], 'Meter#2': [0.0, 0.0, 0.0, 0.0]}, 'e_bat': {'Meter#1': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Storage#1': [0.0, 0.0, -7.8313156e-17, 0.0]}}, 'soc_bat': {'Meter#1': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}}, 'e_bc': {'Meter#1': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}}, 'e_bd': {'Meter#1': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'Storage#1': [0.0, 0.0, 0.0, 0.0]}}, 'delta_bc': {'Meter#1': {'Storage#1': [1.0, 1.0, 1.0, 0.0]}, 'Meter#2': {'Storage#1': [1.0, 1.0, 0.0, 0.0]}}, 'delta_coeff': {'Meter#1': [1.0, 1.0, 0.0, 0.0], 'Meter#2': [1.0, 0.0, 0.0, 0.0]}, 'hp_power': {'Meter#1': {'HP#1': [2.5371775, 0.046444444, 0.046444444, 0.092888889]}, 'Meter#2': {'HP#1': [2.5371775, 1.6110373, 1.4207489, 1.4671934]}}, 'hp_temp_indoor': {'Meter#1': {'HP#1': [18.0, 10.066667, 7.6866667, 6.9726667]}, 'Meter#2': {'HP#1': [18.0, 20.0, 20.0, 20.0]}}, 'hp_power_circulation': {'Meter#1': {'HP#1': [2.5371775, 0.0, 0.0, 0.0]}, 'Meter#2': {'HP#1': [2.5371775, 1.5645928, 1.3743045, 1.3743045]}}, 'hp_power_heating': {'Meter#1': {'HP#1': [0.0, 0.046444444, 0.046444444, 0.092888889]}, 'Meter#2': {'HP#1': [0.0, 0.046444444, 0.046444444, 0.092888889]}}, 'hp_power_tank': {'Meter#1': {'HP#1': [0.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'HP#1': [0.0, 0.0, 0.0, 0.0]}}, 'hp_outlet_temp': {'Meter#1': {'HP#1': [50.0, 0.0, 0.0, 0.0]}, 'Meter#2': {'HP#1': [50.0, 39.733333, 37.333333, 37.333333]}}, 'c_ind2bilateral': {'Meter#1': 0.335, 'Meter#2': 0.116}, 'c_ind2bilateral_without_deg': {'Meter#1': 0.335, 'Meter#2': 0.116}, 'c_ind2bilateral_without_deg_and_p_extra': {'Meter#1': 0.335, 'Meter#2': 0.116}, 'c_ind2bilateral_without_p_extra': {'Meter#1': 0.335, 'Meter#2': 0.116}, 'deg_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0}, 'p_extra_cost2bilateral': {'Meter#1': 0.0, 'Meter#2': 0.0}}
