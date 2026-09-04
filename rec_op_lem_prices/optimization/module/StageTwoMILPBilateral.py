"""
Class for implementing and running the Stage 2 MILP for an energy community.
The implementation is specific to a p2p structure, based on bilateral contracts.
"""
import itertools
import os
import re
import math

from rec_op_lem_prices.configs.configs import (
	MIPGAP,
	SOLVER,
	TIMEOUT
)
from rec_op_lem_prices.optimization.helpers.milp_helpers import (
	dict_none_lists,
	dict_per_param,
	none_lists,
	round_up,
	time_intervals
)
from rec_op_lem_prices.custom_types.stage_two_milp_bilateral_types import (
	BackpackS2BilateralDict,
	OutputsS2BilateralDict
)
from loguru import logger
from pulp import (
	CPLEX_CMD,
	HiGHS_CMD,
	listSolvers,
	LpBinary,
	LpMinimize,
	LpProblem,
	LpStatus,
	lpSum,
	LpVariable,
	GUROBI_CMD,
	pulp,
	value, LpInteger
)


class StageTwoMILPBilateral:
	def __init__(self, backpack: BackpackS2BilateralDict, solver=SOLVER, timeout=TIMEOUT, mipgap=MIPGAP):
		# Indices and sets
		self._horizon = backpack.get('horizon')  # operation period (hours)
		# Parameters
		self._delta_t = backpack.get('delta_t')  # interval settlement duration [h]
		self._l_buy = None  # supply energy tariff [€/kWh]
		self._l_sell = None  # feed in energy tariff [€/kWh]
		self._l_market_buy = backpack.get('l_market_buy')  # market-indexed buying tariff [€/kWh]
		self._l_market_sell = backpack.get('l_market_sell')  # market-indexed selling tariff [€/kWh]
		self._e_c = None  # Meter load profile [kWh]
		self._e_g = None  # Meter generation [kWh]
		self._p_meter_max = None  # power flow limit at the Meter [kW]
		self._eff_bc = {}  # charging efficiency of the batteries [%]
		self._eff_bd = {}  # discharging efficiency of batteries [%]
		self._p_max = {}  # maximum input and output batteries' power [kW]
		self._e_bn = {}  # nominal capacity of the batteries'[kWh]
		self._soc_min = {}  # minimum state of charge of the batteries [%]
		self._soc_max = {}  # maximum state of charge of the batteries [%]
		self._init_e_bat = {}  # initial energy content of the batteries [kWh]
		self._deg_cost = {}  # estimated degradation cost of the batteries of n [€/kWh]
		self._c_ind = None  # objective function values of each Meters' 1st stage MILP solution
		self._l_grid = backpack.get('l_grid')  # access tariff of the local grid between each pair of members [€/kWh]
		self._l_lem = backpack.get('l_lem')  # price for LEM transactions [€/kWh]
		self._big_m = None  # a very big number [kWh]
		self._l_extra = backpack.get('l_extra')  # (fictitious) very high cost of violating p_meter_max
		self._trip_ev = {}  # EV energy consumption, in kWh
		self._min_energy_storage_ev = {}  # Minimum stored energy to be guaranteed for vehicle ev at CPE n, in kWh
		self._battery_capacity_ev = {}  # The battery energy capacity of vehicle ev at CPE n, in kWh
		self._eff_bc_ev = {}  # Charging efficiency of vehicle ev at CPE n, between 0 and 1
		self._eff_bd_ev = {}  # Discharging efficiency of vehicle ev at CPE n, between 0 and 1
		self._init_e_ev = {}  # the initial energy content of the EV, in kWh
		self._pmax_c_ev = {}  # Maximum power charge of vehicle ev at CPE n, in kW
		self._pmax_d_ev = {}  # Maximum power discharge of vehicle ev at CPE n, in kW
		self._bin_ev = {}  # Whether a vehicle ev at CPE n is plugged-in or not (if plugged
		# MILP variables
		self.milp = None  # for storing the MILP formulation
		self.solver = solver  # solver chosen for the MILP
		self.timeout = timeout  # solvers temporal limit to find optimal solution (s)
		self.mipgap = mipgap  # controls the solver's tolerance; intolerant [0 - 1] fully permissive
		self.status = None  # stores the status of the MILP's solution
		self.obj_value = None  # stores the MILP's numeric solution
		self.time_intervals = None  # for number of time intervals per horizon
		self.time_series = None  # for a range of time intervals
		self.set_meters = None  # set with Meters' ID
		self.sets_btm_storage = {}  # stores the Meter's Btm storage assets' ids
		self.sets_btm_ev = {}  # stores the Meter's Btm EVs ids
		self._meters_data = backpack.get('meters')  # data from Meters
		self.second_stage = backpack.get('second_stage')  # indicates if second stage (True) or single stage (False)
		self.strict_pos_coeffs = backpack.get('strict_pos_coeffs')  # no negative coefficients if True
		self.total_share_coeffs = backpack.get('total_share_coeffs')  # share all required in the REC if True
		# EWH
		self._ewh_paramsInput = {}
		self._ewh_dataset = {}
		self.set_ewh = {}
		self.wh_init = {}
		self.ewh_power = {}
		self.delta_t = {}
		self.ewh_start_temp = {}
		self.ewh_capacity = {}
		self.waterHeatCap = {}
		self.heatTransferCoeff = {}
		self.ewh_area = {}
		self.ambTemp = {}
		self.wh_min = {}
		self.wh_max = {}
		self.ewh_min_temp = {}
		self.ewh_max_temp = {}
		self.delta_use = {}
		self.tempSet = {}
		self.bigNumber = {}
		self.regressor_aboveSet_m_temp = {}
		self.regressor_aboveSet_m_delta = {}
		self.regressor_aboveSet_b = {}
		self.regressor_belowSet_m_temp = {}
		self.regressor_belowSet_m_delta = {}
		self.regressor_belowSet_b = {}
		# HVAC
		self._hvac = backpack.get('hvac')
		self.mu = {}  # Building insulation factor
		self.psi = {}  # HVAC temperature efficiency factor
		self.hvac_temp_min = {}  # Min room temperature constraint
		self.hvac_temp_max = {}  # Max room temperature constraint
		self.hvac_init_temp = {}  # Initial room temperature
		self.hvac_capacity = {}  # Maximum HVAC power
		self.T_out = {}  # Outside temperature
		self.set_hvac = {}  # Set of active HVAC units
		self.thermal_resist= {}
		self.thermal_cap = {}
		self.type= {}
		# HP
		self._hp = backpack.get('hp')
		self.set_hp = {}
		self.hp_type = {}
		self.hp_power_rated = {}
		self.hp_capacity_tank = {}
		self.hp_c_p = {}
		self.hp_temp_inlet = {}
		self.hp_temp_desired = {}
		self.hp_temp_out_init = {}
		self.hp_temp_indoor_init = {}
		self.hp_temp_indoor_final = {}
		self.hp_temp_indoor_min = {}
		self.hp_temp_indoor_max = {}
		self.hp_temp_out_min = {}
		self.hp_temp_out_max = {}
		self.hp_u_value = {}
		self.hp_thermal_resistance = {}
		self.hp_h_rad = {}
		self.hp_area_rad = {}
		self.hp_mass_hw_demand = {}
		self.hp_mass_radiator = {}
		self.hp_t_out = {}


	def __define_milp(self):
		"""
		Method to define the second stage MILP problem.
		"""
		logger.debug(f'-- defining the collective (bilateral) MILP problem...')

		# Define a minimization MILP
		self.milp = LpProblem(f'stage2', LpMinimize)

		# Additional temporal variables
		self.time_intervals = time_intervals(self._horizon, self._delta_t)
		self.time_series = range(self.time_intervals)

		# Set of Meters
		self.set_meters = list(self._meters_data.keys())
		self.sets_other_meters = {n: [m for m in self.set_meters if m != n] for n in self.set_meters}

		# For simplicity, unpack Meters' information into lists, by type of data, where each Meter is solely
		# identified by its relative position on the list
		self._l_buy = dict_per_param(self._meters_data, 'l_buy')
		self._l_sell = dict_per_param(self._meters_data, 'l_sell')
		self._e_c = dict_per_param(self._meters_data, 'e_c')
		self._e_g = dict_per_param(self._meters_data, 'e_g')
		self._p_meter_max = dict_per_param(self._meters_data, 'max_p')
		self._big_m = 10 * max(self._p_meter_max.values())
		if self.second_stage:
			self._c_ind = dict_per_param(self._meters_data, 'c_ind')
		else:
			# Unbound the restriction regarding stage 1 cost for single stage runs
			self._c_ind = {k: 1000 for k in self.set_meters}

		# Unpack batteries information
		for n in self.set_meters:
			meter_btm_storage = self._meters_data[n]['btm_storage']
			if meter_btm_storage is not None:
				self.sets_btm_storage[n] = list(meter_btm_storage.keys())
				self._eff_bc[n] = {b: meter_btm_storage[b]['eff_bc'] for b in self.sets_btm_storage[n]}
				self._eff_bd[n] = {b: meter_btm_storage[b]['eff_bd'] for b in self.sets_btm_storage[n]}
				self._p_max[n] = {b: meter_btm_storage[b]['p_max'] for b in self.sets_btm_storage[n]}
				self._e_bn[n] = {b: meter_btm_storage[b]['e_bn'] for b in self.sets_btm_storage[n]}
				self._soc_min[n] = {b: meter_btm_storage[b]['soc_min'] for b in self.sets_btm_storage[n]}
				self._soc_max[n] = {b: meter_btm_storage[b]['soc_max'] for b in self.sets_btm_storage[n]}
				self._init_e_bat[n] = {b: meter_btm_storage[b]['init_e'] for b in self.sets_btm_storage[n]}
				self._deg_cost[n] = {b: meter_btm_storage[b]['degradation_cost'] for b in self.sets_btm_storage[n]}
			else:
				self.sets_btm_storage[n] = []

		# Unpack EVs information
		for n in self.set_meters:
			meter_btm_ev = self._meters_data[n].get('btm_evs')
			if meter_btm_ev is not None:
				self.sets_btm_ev[n] = list(meter_btm_ev.keys())
				self._trip_ev[n] = {ev: meter_btm_ev[ev]['trip_ev'] for ev in self.sets_btm_ev[n]}
				self._min_energy_storage_ev[n] = {ev: meter_btm_ev[ev]['min_energy_storage_ev'] for ev in
												  self.sets_btm_ev[n]}
				self._battery_capacity_ev[n] = {ev: meter_btm_ev[ev]['battery_capacity_ev'] for ev in
												self.sets_btm_ev[n]}
				self._eff_bc_ev[n] = {ev: meter_btm_ev[ev]['eff_bc_ev'] for ev in self.sets_btm_ev[n]}
				self._eff_bd_ev[n] = {ev: meter_btm_ev[ev]['eff_bd_ev'] for ev in self.sets_btm_ev[n]}
				self._init_e_ev[n] = {ev: meter_btm_ev[ev]['init_e_ev'] for ev in self.sets_btm_ev[n]}
				self._pmax_c_ev[n] = {ev: meter_btm_ev[ev]['pmax_c_ev'] for ev in self.sets_btm_ev[n]}
				self._pmax_d_ev[n] = {ev: meter_btm_ev[ev]['pmax_d_ev'] for ev in self.sets_btm_ev[n]}
				self._bin_ev[n] = {ev: meter_btm_ev[ev]['bin_ev'] for ev in self.sets_btm_ev[n]}
			else:
				self.sets_btm_ev[n] = []

		# EWH
		# unpack variables
		for n in self.set_meters:
			try:
				self._ewh = self._meters_data[n]['ewh']
			except KeyError:
				self._ewh = None
			if self._ewh is not None:
				self.set_ewh[n] = list(self._ewh.keys())
				self._ewh_paramsInput[n] = {e: self._ewh[e]['params_input'] for e in self.set_ewh[n]}
				self._ewh_dataset[n] = {e: self._ewh[e]['dataset'] for e in self.set_ewh[n]}
			else:
				self.set_ewh[n] = []

		if bool(self._ewh_dataset):
			# create EWH varBackpacks
			from rec_op_lem_prices.ewh.ewh_flex import ewh_preparation
			global varBackpack

			varBackpack = {}
			for n in self.set_meters:
				self._ewh = self._meters_data[n]['ewh']

				if self._ewh is not None:
					varBackpack[n] = {
						e: ewh_preparation(self._ewh_paramsInput[n][e], self._ewh_dataset[n][e], resample='1h')
						for e in self.set_ewh[n]
					}

					self.wh_init[n] = {e: varBackpack[n][e]['wh_init'] for e in self.set_ewh[n]}
					self.ewh_power[n] = {e: varBackpack[n][e]['ewh_power'] for e in self.set_ewh[n]}
					self.delta_t[n] = {e: varBackpack[n][e]['delta_t'] for e in self.set_ewh[n]}
					self.ewh_start_temp[n] = {e: varBackpack[n][e]['ewh_start_temp'] for e in self.set_ewh[n]}
					self.ewh_capacity[n] = {e: varBackpack[n][e]['ewh_capacity'] for e in self.set_ewh[n]}
					self.waterHeatCap[n] = {e: varBackpack[n][e]['waterHeatCap'] for e in self.set_ewh[n]}
					self.heatTransferCoeff[n] = {e: varBackpack[n][e]['heatTransferCoeff'] for e in self.set_ewh[n]}
					self.ewh_area[n] = {e: varBackpack[n][e]['ewh_area'] for e in self.set_ewh[n]}
					self.ambTemp[n] = {e: varBackpack[n][e]['ambTemp'] for e in self.set_ewh[n]}
					self.wh_min[n] = {e: varBackpack[n][e]['wh_min'] for e in self.set_ewh[n]}
					self.wh_max[n] = {e: varBackpack[n][e]['wh_max'] for e in self.set_ewh[n]}
					self.ewh_min_temp[n] = {e: varBackpack[n][e]['ewh_min_temp'] for e in self.set_ewh[n]}
					self.ewh_max_temp[n] = {e: varBackpack[n][e]['ewh_max_temp'] for e in self.set_ewh[n]}
					self.delta_use[n] = {e: varBackpack[n][e]['delta_use'] for e in self.set_ewh[n]}
					self.tempSet[n] = {e: varBackpack[n][e]['tempSet'] for e in self.set_ewh[n]}
					self.bigNumber[n] = {e: varBackpack[n][e]['bigNumber'] for e in self.set_ewh[n]}
					self.regressor_aboveSet_m_temp[n] = \
						{e: varBackpack[n][e]['regressor_aboveSet_m_temp'] for e in self.set_ewh[n]}
					self.regressor_aboveSet_m_delta[n] = \
						{e: varBackpack[n][e]['regressor_aboveSet_m_delta'] for e in self.set_ewh[n]}
					self.regressor_aboveSet_b[n] = \
						{e: varBackpack[n][e]['regressor_aboveSet_b'] for e in self.set_ewh[n]}
					self.regressor_belowSet_m_temp[n] = \
						{e: varBackpack[n][e]['regressor_belowSet_m_temp'] for e in self.set_ewh[n]}
					self.regressor_belowSet_m_delta[n] = \
						{e: varBackpack[n][e]['regressor_belowSet_m_delta'] for e in self.set_ewh[n]}
					self.regressor_belowSet_b[n] = \
						{e: varBackpack[n][e]['regressor_belowSet_b'] for e in self.set_ewh[n]}
				else:
					varBackpack[n] = []

		# Unpack HVAC information
		for n in self.set_meters:
			self._hvac = self._meters_data[n].get('hvac')
			if self._hvac is not None:
				self.set_hvac[n] = list(self._hvac.keys())
				self.mu[n] = {h: self._hvac[h]['mu'] for h in self.set_hvac[n]}
				self.psi[n] = {h: self._hvac[h]['psi'] for h in self.set_hvac[n]}
				self.hvac_capacity[n] = {h: self._hvac[h]['hvac_capacity'] for h in self.set_hvac[n]}
				self.hvac_temp_min[n] = {h: self._hvac[h]['temp_min'] for h in self.set_hvac[n]}
				self.hvac_temp_max[n] = {h: self._hvac[h]['temp_max'] for h in self.set_hvac[n]}
				self.hvac_init_temp[n] = {h: self._hvac[h]['init_temp'] for h in self.set_hvac[n]}
				self.T_out[n] = {h: self._hvac[h]['t_out'] for h in self.set_hvac[n]}
				self.thermal_resist[n] = {h: self._hvac[h]['thermal_resist'] for h in self.set_hvac[n]}
				self.thermal_cap[n] = {h: self._hvac[h]['thermal_cap'] for h in self.set_hvac[n]}
				self.type[n] = {h: self._hvac[h]['type'] for h in self.set_hvac[n]}
			else:
				self.set_hvac[n] = []

		#Unpack HP information
		for n in self.set_meters:
			self._hp = self._meters_data[n].get('hp')
			if self._hp is not None:
				self.set_hp[n] = list(self._hp.keys())
				self.hp_type[n] = {hp: self._hp[hp]['type'] for hp in self.set_hp[n]}
				self.hp_power_rated[n] = {hp: self._hp[hp]['power_rated'] for hp in self.set_hp[n]}
				self.hp_capacity_tank[n] = {hp: self._hp[hp]['capacity_tank'] for hp in self.set_hp[n]}
				self.hp_c_p[n] = {hp: self._hp[hp]['c_p'] for hp in self.set_hp[n]}
				self.hp_temp_inlet[n] = {hp: self._hp[hp]['temp_inlet'] for hp in self.set_hp[n]}
				self.hp_temp_desired[n] = {hp: self._hp[hp]['temp_desired'] for hp in self.set_hp[n]}
				self.hp_temp_out_init[n] = {hp: self._hp[hp]['temp_out_init'] for hp in self.set_hp[n]}
				self.hp_temp_indoor_init[n] = {hp: self._hp[hp]['temp_indoor_init'] for hp in self.set_hp[n]}
				self.hp_temp_indoor_final[n] = {hp: self._hp[hp]['temp_indoor_final'] for hp in self.set_hp[n]}
				self.hp_temp_indoor_min[n] = {hp: self._hp[hp]['temp_indoor_min'] for hp in self.set_hp[n]}
				self.hp_temp_indoor_max[n] = {hp: self._hp[hp]['temp_indoor_max'] for hp in self.set_hp[n]}
				self.hp_temp_out_min[n] = {hp: self._hp[hp]['temp_out_min'] for hp in self.set_hp[n]}
				self.hp_temp_out_max[n] = {hp: self._hp[hp]['temp_out_max'] for hp in self.set_hp[n]}
				self.hp_u_value[n] = {hp: self._hp[hp]['u_value'] for hp in self.set_hp[n]}
				self.hp_thermal_resistance[n] = {hp: self._hp[hp]['thermal_resistance'] for hp in self.set_hp[n]}
				self.hp_h_rad[n] = {hp: self._hp[hp]['h_rad'] for hp in self.set_hp[n]}
				self.hp_area_rad[n] = {hp: self._hp[hp]['area_rad'] for hp in self.set_hp[n]}
				self.hp_mass_hw_demand[n] = {hp: self._hp[hp]['mass_hw_demand'] for hp in self.set_hp[n]}
				self.hp_mass_radiator[n] = {hp: self._hp[hp]['mass_radiator'] for hp in self.set_hp[n]}
				self.hp_t_out[n] = {hp: self._hp[hp]['t_out'] for hp in self.set_hp[n]}
			else:
				self.set_hp[n] = []

		# Initialize the decision variables
		# energy supplied to n from its retailer [kWh]
		e_sup_retail = dict_none_lists(self.time_intervals, self.set_meters)
		# energy surplus sold by n to its retailer [kWh]
		e_sur_retail = dict_none_lists(self.time_intervals, self.set_meters)
		# energy supplied to n at a market-indexed price [kWh]
		e_sup_market = dict_none_lists(self.time_intervals, self.set_meters)
		# energy surplus sold by n at a market-indexed price [kWh]
		e_sur_market = dict_none_lists(self.time_intervals, self.set_meters)
		# when True allows supply when false allows surplus
		delta_sup = dict_none_lists(self.time_intervals, self.set_meters)
		# energy bought locally by n from m
		e_pur = {n: dict_none_lists(self.time_intervals, self.sets_other_meters[n]) for n in self.set_meters}
		# energy sold locally by n to m
		e_sale = {n: dict_none_lists(self.time_intervals, self.sets_other_meters[n]) for n in self.set_meters}
		# net consumption at meter n [kWh]
		e_cmet = dict_none_lists(self.time_intervals, self.set_meters)
		# energy self-consumed by n, allocated from m (in theory, g.t.e. that value)
		e_slc = {n: dict_none_lists(self.time_intervals, self.sets_other_meters[n]) for n in self.set_meters}
		# consumption at meter n (in theory, g.t.e. that value)
		e_consumed = dict_none_lists(self.time_intervals, self.set_meters)
		# consumed energy bought locally by n (in theory, g.t.e. that value)
		e_alc = dict_none_lists(self.time_intervals, self.set_meters)
		# auxiliary binary variable for defining self-consumed energy by n
		delta_slc = dict_none_lists(self.time_intervals, self.set_meters)
		# for defining e_consumed when a particular self._l_grid[t] is negative
		delta_cmet = dict_none_lists(self.time_intervals, self.set_meters)
		# for defining e_alc when a particular self._l_grid[t] is negative
		delta_alc = dict_none_lists(self.time_intervals, self.set_meters)
		# extra power flow at n, beyond p_meter_max [kW]
		p_extra = dict_none_lists(self.time_intervals, self.set_meters)
		# energy stored by the batteries of n [kWh]
		e_bat = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		# SOC of the batteries of n [%]
		soc_bat = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		# energy charged by n's batteries [kWh]
		e_bc = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		# energy discharged by n's batteries [kWh]
		e_bd = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		# when True allows charge, else discharge
		delta_bc = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		# EV decision variables
		# energy stored in ev [kWh]
		ev_stored = {n: dict_none_lists(self.time_intervals, self.sets_btm_ev[n]) for n in self.set_meters}
		# power charge of ev [kW]
		p_ev_charge = {n: dict_none_lists(self.time_intervals, self.sets_btm_ev[n]) for n in self.set_meters}
		# power discharge of ev [kW]
		p_ev_discharge = {n: dict_none_lists(self.time_intervals, self.sets_btm_ev[n]) for n in self.set_meters}
		if self.strict_pos_coeffs:
			# auxiliary binary variable for imposing positive allocation coefficients
			delta_coeff = dict_none_lists(self.time_intervals, self.set_meters)
		if self.total_share_coeffs:
			# auxiliary binary variable for signaling if the REC has a surplus or a deficit
			delta_rec_balance = none_lists(self.time_intervals)
			# auxiliary binary variable for signaling if a meter has a surplus or a deficit
			delta_meter_balance = dict_none_lists(self.time_intervals, self.set_meters)
		# EWH - Initialize decision variables
		if bool(self._ewh_dataset):
			temp = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			w_tot = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			w_in = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			w_loss = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			delta_in = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			w_water = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			costComfort = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			binAux = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			energyEWH = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
		# HVAC - Initialize decision variables
		if self.set_hvac is not None:
			hvac_temp = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_power = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			delta_hvac = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_active = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_cost_comfort = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_mode = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_mode_heat = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_mode_off = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			hvac_mode_cool = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}

		# HP - Initialize decision variables
		if self.set_hp is not None:
			self.hp_temp_indoor = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_temp_outlet = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_power = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_active = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_cost_comfort = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_op_mode = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.heating_kwh = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.circulation_kw = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.tank_heating_kwh = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_temp_return = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}
			self.hp_lost_power = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in self.set_meters}



		# Define the decision variables as puLP objets
		if self.total_share_coeffs:
			for t in self.time_series:
				increment = f't{t:03d}'
				delta_rec_balance[t] = LpVariable('delta_rec_balance_' + increment, cat=LpBinary)

		t_n_series = itertools.product(self.set_meters, self.time_series)  # iterates over each Meter and each time step
		for n, t in t_n_series:
			increment = f'{n}_t{t:03d}'
			e_sup_retail[n][t] = LpVariable('e_sup_retail_' + increment, lowBound=0)
			e_sur_retail[n][t] = LpVariable('e_sur_retail_' + increment, lowBound=0)
			e_sup_market[n][t] = LpVariable('e_sup_market_' + increment, lowBound=0)
			e_sur_market[n][t] = LpVariable('e_sur_market_' + increment, lowBound=0)
			delta_sup[n][t] = LpVariable('delta_sup_' + increment, cat=LpBinary)
			e_cmet[n][t] = LpVariable('e_cmet_' + increment)
			e_consumed[n][t] = LpVariable('e_consumed_' + increment, lowBound=0)
			e_alc[n][t] = LpVariable('e_alc_' + increment, lowBound=0)
			delta_slc[n][t] = LpVariable('delta_slc_' + increment, cat=LpBinary)
			delta_cmet[n][t] = LpVariable('delta_cmet_' + increment, cat=LpBinary)
			delta_alc[n][t] = LpVariable('delta_alc_' + increment, cat=LpBinary)
			p_extra[n][t] = LpVariable('p_extra_' + increment, lowBound=0)
			if self.strict_pos_coeffs:
				delta_coeff[n][t] = LpVariable('delta_coeff_' + increment, cat=LpBinary)
			if self.total_share_coeffs:
				delta_meter_balance[n][t] = LpVariable('delta_meter_balance_' + increment, cat=LpBinary)
			for b in self.sets_btm_storage[n]:
				increment = f'{n}_{b}_t{t:03d}'
				e_bat[n][b][t] = LpVariable('e_bat_' + increment, lowBound=0)
				soc_bat[n][b][t] = LpVariable('soc_bat_' + increment, lowBound=0)
				e_bc[n][b][t] = LpVariable('e_bc_' + increment, lowBound=0)
				e_bd[n][b][t] = LpVariable('e_bd_' + increment, lowBound=0)
				delta_bc[n][b][t] = LpVariable('delta_bc_' + increment, cat=LpBinary)
			for m in self.sets_other_meters[n]:
				increment = f'{n}_{m}_t{t:03d}'
				e_pur[n][m][t] = LpVariable('e_pur_' + increment, lowBound=0)
				e_sale[n][m][t] = LpVariable('e_sale_' + increment, lowBound=0)
				e_slc[n][m][t] = LpVariable('e_slc_' + increment, lowBound=0)
			for ev in self.sets_btm_ev[n]:
				increment = f'{n}_{ev}_t{t:03d}'
				ev_stored[n][ev][t] = LpVariable('ev_stored_' + increment, lowBound=0)
				p_ev_charge[n][ev][t] = LpVariable('p_ev_charge_' + increment, lowBound=0)
				p_ev_discharge[n][ev][t] = LpVariable('p_ev_discharge_' + increment, lowBound=0)
			# EWH decision variables
			if bool(self._ewh_dataset):
				for e in self.set_ewh[n]:
					increment = f'{n}_{e}_t{t:07d}'
					# Temperature of water at EWH outlet at the beginning of time interval t (°C)
					temp[n][e][t] = LpVariable(f'temp_' + increment, lowBound=0)
					# Total energy balance of prosumer’s EWH at time interval t (kWh)
					w_tot[n][e][t] = LpVariable(f'w_tot_' + increment, lowBound=0)
					# Energy into the prosumer’s EWH at time interval t (kWh)
					w_in[n][e][t] = LpVariable(f'w_in_' + increment, lowBound=0)
					# Thermal energy losses at time interval t (kWh)
					w_loss[n][e][t] = LpVariable(f'w_loss_' + increment)
					# Binary variable for EWH operation status (1 = ON, 0 = OFF)
					delta_in[n][e][t] = LpVariable(f'delta_in_' + increment, lowBound=0, upBound=1)
					# Amount of energy stored in the EWH after usage and mixing with inlet
					w_water[n][e][t] = LpVariable(f'w_water_' + increment, lowBound=0)
					# Extra cost associated with water temperature reaching below comfort
					costComfort[n][e][t] = LpVariable(f'costComfort_' + increment, lowBound=0)
					# Binary Variable for if-else expression 15
					binAux[n][e][t] = LpVariable(f'binAux_' + increment, cat=LpBinary)
					# Pricing of that specific energy usage
					energyEWH[n][e][t] = LpVariable(f'energyEWH_' + increment, lowBound=0)
			if self.set_hvac is not None:
				for h in self.set_hvac[n]:
					increment = f'{n}_{h}_t{t:03d}'
					hvac_temp[n][h][t] = LpVariable(f'hvac_temp_' + increment, lowBound=0)
					hvac_power[n][h][t] = LpVariable(f'hvac_power_' + increment, lowBound=0)
					delta_hvac[n][h][t] = LpVariable(f'delta_hvac_' + increment, lowBound=0, upBound=5, cat=LpInteger)
					hvac_active[n][h][t] = LpVariable(f'hvac_active_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					hvac_mode[n][h][t] = LpVariable(f'hvac_mode_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					hvac_mode_heat[n][h][t] = LpVariable(f'hvac_mode_heat_' + increment, lowBound=0, upBound=1,
														 cat=LpBinary)
					hvac_mode_off[n][h][t] = LpVariable(f'hvac_mode_off_' + increment, lowBound=0, upBound=1,
														cat=LpBinary)
					hvac_mode_cool[n][h][t] = LpVariable(f'hvac_mode_cool_' + increment, lowBound=0, upBound=1,
														 cat=LpBinary)
					hvac_cost_comfort[n][h][t] = LpVariable(f'hvac_cost_comfort_' + increment, lowBound=0)

			if self.set_hp is not None:
				for hp in self.set_hp[n]:
					increment = f'{n}_{hp}_t{t:03d}'
					self.hp_temp_indoor[n][hp][t] = LpVariable(f'hp_temp_indoor_' + increment, lowBound=0)
					self.hp_temp_outlet[n][hp][t] = LpVariable(f'hp_temp_outlet_' + increment, lowBound=0)
					self.hp_power[n][hp][t] = LpVariable(f'power_hp_' + increment, lowBound=0)
					self.hp_active[n][hp][t] = LpVariable(f'hp_active_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					self.hp_cost_comfort[n][hp][t] = LpVariable(f'hp_cost_comfort_' + increment, lowBound=0)
					self.hp_active[n][hp][t] = LpVariable(f'hp_active_' + increment, cat=LpBinary)
					self.heating_kwh[n][hp][t] = LpVariable(f'hp_power_heating_' + increment, lowBound=0)
					self.circulation_kw[n][hp][t] = LpVariable(f'hp_power_circulation_' + increment, lowBound=0)
					self.tank_heating_kwh[n][hp][t] = LpVariable(f'hp_power_tank_' + increment, lowBound=0)
					self.hp_temp_return[n][hp][t] = LpVariable(f'hp_temp_return_' + increment, lowBound=0)
					self.hp_lost_power[n][hp][t] = LpVariable(f'hp_lost_power_' + increment, lowBound=0)

		# Eq. 10: Objective Function
		objective = lpSum(
			lpSum(
				e_sup_retail[n][t] * self._l_buy[n][t] - e_sur_retail[n][t] * self._l_sell[n][t]
				+ e_sup_market[n][t] * self._l_market_buy[t] - e_sur_market[n][t] * self._l_market_sell[t]
				+ lpSum(e_slc[n][m][t] * self._l_grid[n][m][t] for m in self.sets_other_meters[n])
				+ p_extra[n][t] * self._l_extra
				+ lpSum(self._deg_cost[n][b] * e_bd[n][b][t] for b in self.sets_btm_storage[n])
				+ lpSum(costComfort[n][e][t] * 100 for e in self.set_ewh[n])
				for n in self.set_meters
			)

			for t in self.time_series
		)

		for t in self.time_series:
			if t != 0:
				objective += lpSum(hvac_cost_comfort[n][h][t] * 1 for n in self.set_meters for h in self.set_hvac[n]) + lpSum(self.hp_cost_comfort[n][hp][t] * 1 for hp in self.set_hp[n])

		self.milp += objective, 'Objective Function'

		# Eq. 11-34: Constraints
		if self.total_share_coeffs:
			for t in self.time_series:
				increment = f'{t:03d}'
				# Eq. 32
				self.milp += \
					lpSum(e_cmet[n][t] for n in self.set_meters) >= - self._big_m * delta_rec_balance[t], \
					'Check_REC_surplus_' + increment

				# Eq. 33
				self.milp += \
					lpSum(e_cmet[n][t] for n in self.set_meters) <= self._big_m * (1 - delta_rec_balance[t]), \
					'Check_REC_deficit_' + increment

		for n, t in itertools.product(self.set_meters, self.time_series):
			for m in self.sets_other_meters[n]:
				increment = f'{n}_{m}_t{t:03d}'
				# Eq. 11
				self.milp += \
					e_sale[n][m][t] == e_pur[m][n][t], \
					'Market_equilibrium_' + increment

				if all([lg[t] >= 0 for _, lg in self._l_grid[n].items()]):
					# Eq. 35
					self.milp += \
						e_slc[n][m][t] >= e_pur[n][m][t] - e_sale[n][m][t] - self._big_m * delta_slc[n][t], \
						'Self_consumed_is_allocated_' + increment

					# Eq. 36
					self.milp += \
						e_slc[n][m][t] <= e_pur[n][m][t] - e_sale[n][m][t] + self._big_m * (1 - delta_slc[n][t]), \
						'Self_consumed_is_consumed_' + increment

			increment = f'{n}_t{t:03d}'
			# Eq. 12
			self.milp += \
				e_cmet[n][t] == \
				e_sup_retail[n][t] + e_sup_market[n][t] - e_sur_retail[n][t] - e_sur_market[n][t] \
				+ lpSum(e_pur[n][m][t] - e_sale[n][m][t] for m in self.sets_other_meters[n]), \
				'Equilibrium_' + increment

			# Eq. 13
			self.milp += \
				e_cmet[n][t] == self._e_c[n][t] - self._e_g[n][t] \
				+ lpSum(e_bc[n][b][t] - e_bd[n][b][t] for b in self.sets_btm_storage[n]) \
				+ lpSum(p_ev_charge[n][ev][t] * self._delta_t - p_ev_discharge[n][ev][t] * self._delta_t
				 for ev in self.sets_btm_ev[n]) \
				+ lpSum(- varBackpack[n][e]['original_load'][t] + energyEWH[n][e][t] for e in self.set_ewh[n]) + \
				lpSum(hvac_power[n][h][t] for h in self.set_hvac[n]) + lpSum(self.hp_power[n][hp][t]for hp in self.set_hp[n]), \
				'C_met_' + increment

			# Eq. 14
			self.milp += \
				- p_extra[n][t] - self._p_meter_max[n] <= e_cmet[n][t] * 1 / self._delta_t, \
				'P_flow_low_limit_' + increment

			self.milp += \
				e_cmet[n][t] * 1 / self._delta_t <= p_extra[n][t] + self._p_meter_max[n], \
				'P_flow_high_limit_' + increment

			# Eq. 15
			self.milp += \
				e_sup_retail[n][t] + e_sup_market[n][t] <= self._big_m * delta_sup[n][t], \
				'Supply_ON_' + increment

			self.milp += \
				e_sur_retail[n][t] + e_sur_market[n][t] <= self._big_m * (1 - delta_sup[n][t]), \
				'Supply_OFF_' + increment

			if all([lg[t] >= 0 for _, lg in self._l_grid[n].items()]):
				# Eq. 20
				self.milp += \
					e_consumed[n][t] >= e_cmet[n][t], \
					'Consumption_' + increment

				# Eq. 21
				self.milp += \
					e_alc[n][t] >= lpSum(e_pur[n][m][t] - e_sale[n][m][t] for m in self.sets_other_meters[n]), \
					'Allocated_energy_' + increment

				# Eq. 22
				self.milp += \
					lpSum(e_slc[n][m][t] for m in self.sets_other_meters[n]) >= \
					e_consumed[n][t] - self._big_m * (1 - delta_slc[n][t]), \
					'Self_consumption_1_' + increment

				# Eq. 23
				self.milp += \
					lpSum(e_slc[n][m][t] for m in self.sets_other_meters[n]) >= \
					e_alc[n][t] - self._big_m * delta_slc[n][t], \
					'Self_consumption_2_' + increment

				# Eq. aux
				self.milp += \
					delta_cmet[n][t] == 0, \
					'Consumption_bin_' + increment

				# Eq. aux
				self.milp += \
					delta_alc[n][t] == 0, \
					'Allocated_energy_bin_' + increment

			else:
				# Eq. 24
				self.milp += \
					e_consumed[n][t] <= e_cmet[n][t] + self._big_m * delta_cmet[n][t], \
					'Consumption_1_' + increment

				# Eq. 25
				self.milp += \
					e_consumed[n][t] <= self._big_m * (1 - delta_cmet[n][t]), \
					'Consumption_2_' + increment

				# Eq. 26
				self.milp += \
					e_alc[n][t] <= lpSum(e_pur[n][m][t] - e_sale[n][m][t] for m in self.sets_other_meters[n]) \
					+ self._big_m * delta_alc[n][t], \
					'Allocated_energy_1_' + increment

				# Eq. 27
				self.milp += \
					e_alc[n][t] <= self._big_m * (1 - delta_alc[n][t]), \
					'Allocated_energy_2_' + increment

				# Eq. 28
				self.milp += \
					lpSum(e_slc[n][m][t] for m in self.sets_other_meters[n]) <= e_consumed[n][t], \
					'Self_consumption_1_' + increment

				# Eq. 29
				self.milp += \
					lpSum(e_slc[n][m][t] for m in self.sets_other_meters[n]) <= e_alc[n][t], \
					'Self_consumption_2_' + increment

				# Eq. aux
				self.milp += \
					delta_slc[n][t] == 0, \
					'Self_consumed_energy_bin_' + increment

			if self.strict_pos_coeffs:
				# Eq. 30
				self.milp += \
					lpSum(e_sale[n][m][t] - e_pur[n][m][t] for m in self.sets_other_meters[n]) <= \
					-e_cmet[n][t] + self._big_m * delta_coeff[n][t], \
					'Positive_coefficients_1_' + increment

				# Eq. 31
				self.milp += \
					lpSum(e_sale[n][m][t] - e_pur[n][m][t] for m in self.sets_other_meters[n]) <= \
					self._big_m * (1 - delta_coeff[n][t]), \
					'Positive_coefficients_2_' + increment

			if self.total_share_coeffs:
				# Eq. 34
				self.milp += \
					e_cmet[n][t] >= - self._big_m * delta_meter_balance[n][t], \
					'Check_meter_surplus_' + increment

				# Eq. 35
				self.milp += \
					e_cmet[n][t] <= self._big_m * (1 - delta_meter_balance[n][t]), \
					'Check_meter_deficit_' + increment

				# Eq. 36
				self.milp += \
					lpSum(e_sale[n][m][t] for m in self.sets_other_meters[n]) >= \
					- e_cmet[n][t] - self._big_m * (1 - delta_meter_balance[n][t] + delta_rec_balance[t]), \
					'Share_all_surplus_low_' + increment

				# Eq. 37
				self.milp += \
					lpSum(e_sale[n][m][t] for m in self.sets_other_meters[n]) <= \
					- e_cmet[n][t] + self._big_m * (1 - delta_meter_balance[n][t] + delta_rec_balance[t]), \
					'Share_all_surplus_high_' + increment

				# Eq. 38
				self.milp += \
					lpSum(e_pur[n][m][t] for m in self.sets_other_meters[n]) >= \
					e_cmet[n][t] - self._big_m * (1 - delta_rec_balance[t] + delta_meter_balance[n][t]), \
					'Buy_all_deficit_low_' + increment

				# Eq. 39
				self.milp += \
					lpSum(e_pur[n][m][t] for m in self.sets_other_meters[n]) <= \
					e_cmet[n][t] + self._big_m * (1 - delta_rec_balance[t] + delta_meter_balance[n][t]), \
					'Buy_all_deficit_high_' + increment

			for b in self.sets_btm_storage[n]:
				increment = f'{n}_{b}_t{t:03d}'

				if self._e_bn[n][b] > 0:
					# Eq. 16
					energy_update = e_bc[n][b][t] * self._eff_bc[n][b] \
					                - e_bd[n][b][t] * 1 / self._eff_bd[n][b]
					if t == 0:
						self.milp += \
							e_bat[n][b][t] == self._init_e_bat[n][b] + energy_update, \
							'SOC_update_' + increment
					else:
						self.milp += \
							e_bat[n][b][t] == e_bat[n][b][t - 1] + energy_update, \
							'SOC_update_' + increment

					# Eq. 17
					self.milp += \
						soc_bat[n][b][t] == e_bat[n][b][t] * 100 / self._e_bn[n][b], \
						'Energy_to_SOC_' + increment

					self.milp += \
						soc_bat[n][b][t] >= self._soc_min[n][b], \
						'Minimum_SOC_' + increment

					self.milp += \
						soc_bat[n][b][t] <= self._soc_max[n][b], \
						'Maximum_SOC_' + increment

					# Eq. 18
					self.milp += \
						e_bc[n][b][t] * 1 / self._delta_t <= self._p_max[n][b] * delta_bc[n][b][t], \
						'Charge_rate_limit_' + increment

					self.milp += \
						e_bd[n][b][t] * 1 / self._delta_t <= self._p_max[n][b] * (1 - delta_bc[n][b][t]), \
						'Discharge_rate_limit' + increment

		# EVs constraints
			for ev in self.sets_btm_ev[n]:
				increment = f'{n}_{ev}_t{t:03d}'
				# Eq. 41
				if t == 0:
					self.milp += ev_stored[n][ev][t] == self._init_e_ev[n][ev] + self._eff_bc_ev[n][ev] * \
								 p_ev_charge[n][ev][t] \
								 * self._delta_t - (1 / self._eff_bd_ev[n][ev]) * p_ev_discharge[n][ev][
									 t] * self._delta_t \
								 - self._trip_ev[n][ev][t], \
								 'EV_balance_' + increment
				else:
					self.milp += ev_stored[n][ev][t] == ev_stored[n][ev][t - 1] + self._eff_bc_ev[n][ev] * \
								 p_ev_charge[n][ev][
									 t] * \
								 self._delta_t - (1 / self._eff_bd_ev[n][ev]) * p_ev_discharge[n][ev][t] * \
								 self._delta_t - self._trip_ev[n][ev][t], \
								 'EV_balance_' + increment

				# Eq. 42
				self.milp += (1 / self._eff_bd_ev[n][ev]) * p_ev_discharge[n][ev][t] <= self._pmax_d_ev[n][ev] * \
							 self._bin_ev[n][ev][t], 'EV_Discharging_limit_' + increment

				# Eq. 43
				self.milp += self._eff_bc_ev[n][ev] * p_ev_charge[n][ev][t] <= self._pmax_c_ev[n][ev] * \
							 self._bin_ev[n][ev][t], 'EV_Charging_limit_' + increment

				# Eq. 44
				self.milp += ev_stored[n][ev][t] <= self._battery_capacity_ev[n][
					ev], 'EV_Max_capacity_' + increment

				# Eq. 45
				self.milp += ev_stored[n][ev][t] >= self._min_energy_storage_ev[n][
					ev], 'EV_Min_capacity_' + increment

		for n in self.set_meters:
			increment = f'{n}'

			# Eq. 19
			self.milp += lpSum(
				e_sup_retail[n][t] * self._l_buy[n][t] - e_sur_retail[n][t] * self._l_sell[n][t]
				+ e_sup_market[n][t] * self._l_market_buy[t] - e_sur_market[n][t] * self._l_market_sell[t]
				+ lpSum(e_slc[n][m][t] * self._l_grid[n][m][t] for m in self.sets_other_meters[n])
				+ p_extra[n][t] * self._l_extra
				+ lpSum(self._deg_cost[n][b] * e_bd[n][b][t] for b in self.sets_btm_storage[n])
				+ (lpSum(e_pur[n][m][t] - e_sale[n][m][t] for m in self.sets_other_meters[n])) * self._l_lem[t]
				for t in self.time_series
			) <= round_up(self._c_ind[n]), 'Stage_1_cost_' + increment

		# EWH constraints
		if bool(self._ewh_dataset):
			for n, t in itertools.product(self.set_meters, self.time_series):
				for e in self.set_ewh[n]:
					# Eq. (1)
					if t == 0:
						self.milp += w_tot[n][e][t] == self.wh_init[n][e], \
							f'Constraint_1_{n}_{e}_{t:07d}'
					else:
						self.milp += w_tot[n][e][t] == w_water[n][e][t - 1] + w_in[n][e][t - 1] - w_loss[n][e][t - 1], \
							f'Constraint_1_{n}_{e}_{t:07d}'
					# Eq. (2)
					self.milp += \
						w_in[n][e][t] == \
						self.ewh_power[n][e] * self.delta_t[n][e] * delta_in[n][e][t] * self.delta_t[n][e] * 60, \
							f'Constraint_2_{n}_{e}_{t:07d}'
					# Eq. (3) Pricing/Energy
					self.milp += energyEWH[n][e][t] == delta_in[n][e][t] * self.ewh_power[n][e] * self.delta_t[n][e], \
						f'Constraint_3_{n}_{e}_{t:07d}'
					# Eq. (4)
					if t == 0:
						self.milp += temp[n][e][t] == self.ewh_start_temp[n][e], f'Constraint_4_{n}_{e}_{t:07d}'
					else:
						self.milp += \
							temp[n][e][t] == \
							w_tot[n][e][t] * 3600 / \
							(self.delta_t[n][e] * 60) / \
							(self.ewh_capacity[n][e] * self.waterHeatCap[n][e]), \
								f'Constraint_4_{n}_{e}_{t:07d}'
					# Eq. (5)
					self.milp += \
						w_loss[n][e][t] == \
						self.heatTransferCoeff[n][e] * \
						self.ewh_area[n][e] * \
						(temp[n][e][t] - self.ambTemp[n][e]) * \
						self.delta_t[n][e] * \
						self.delta_t[n][e] * 60, \
							f'Constraint_5_{n}_{e}_{t:07d}'
					# Eq. (6)
					self.milp += self.wh_min[n][e] <= w_tot[n][e][t], f'Constraint_6.1_{n}_{e}_{t:07d}'
					self.milp += w_tot[n][e][t] <= self.wh_max[n][e], f'Constraint_6.2_{n}_{e}_{t:07d}'
					self.milp += self.ewh_min_temp[n][e] <= temp[n][e][t], f'Constraint_6.3_{n}_{e}_{t:07d}'
					self.milp += temp[n][e][t] <= self.ewh_max_temp[n][e], f'Constraint_6.4_{n}_{e}_{t:07d}'

					# Eq.(7) assure that in the (t) period after the end of hot water usage (t-1),
					# the EWH has, at least, 80L @ 45ºC [n][e][t]
					if (self.delta_use[n][e][t] - self.delta_use[n][e][t - 1] != 0) & \
							(self.delta_use[n][e][t] - self.delta_use[n][e][t - 1] == -self.delta_use[n][e][t-1]):
						# if delta_use[n][e][t] - delta_use[t-1] < 0:
						self.milp += \
							w_tot[n][e][t] >= \
							self.tempSet[n][e] * 1.005 * \
							self.ewh_capacity[n][e] * \
							self.waterHeatCap[n][e] / 3600 * \
							self.delta_t[n][e] * 60 - \
							costComfort[n][e][t], \
								f'Constraint_7.1_{n}_{e}_{t:07d}'
						self.milp += \
							w_tot[n][e][t-1] >= \
							self.tempSet[n][e] * 1.005 * \
							self.ewh_capacity[n][e] * \
							self.waterHeatCap[n][e] / 3600 * \
							self.delta_t[n][e] * 60 - \
							costComfort[n][e][t-1], \
								f'Constraint_7.2_{n}_{e}_{t:07d}'

					# Eq.(8) Internal water energy after usage
					if self.delta_use[n][e][t] > 0:
						# binary definition with temp[n][e][t]
						self.milp += temp[n][e][t] >= \
									 self.tempSet[n][e] - self.bigNumber[n][e] * (1 - binAux[n][e][t]), \
							f'Constraint_8.1_{n}_{e}_{t:07d}'
						self.milp += temp[n][e][t] <= \
									 self.tempSet[n][e] + self.bigNumber[n][e] * binAux[n][e][t], \
							f'Constraint_8.2_{n}_{e}_{t:07d}'
						# if temp[n][e][t] > tempSet
						self.milp += w_water[n][e][t] >= \
									 self.regressor_aboveSet_m_temp[n][e] * temp[n][e][t] + \
									 self.regressor_aboveSet_m_delta[n][e] * self.delta_use[n][e][t] + \
									 self.regressor_aboveSet_b[n][e] - \
									 self.bigNumber[n][e] * (1 - binAux[n][e][t]), \
							f'Constraint_8.3_{n}_{e}_{t:07d}'
						self.milp += w_water[n][e][t] <= \
									 self.regressor_aboveSet_m_temp[n][e] * temp[n][e][t] + \
									 self.regressor_aboveSet_m_delta[n][e] * self.delta_use[n][e][t] + \
									 self.regressor_aboveSet_b[n][e] + \
									 self.bigNumber[n][e] * (1 - binAux[n][e][t]), \
							f'Constraint_8.4_{n}_{e}_{t:07d}'
						# else
						self.milp += w_water[n][e][t] >= \
									 self.regressor_belowSet_m_temp[n][e] * temp[n][e][t] + \
									 self.regressor_belowSet_m_delta[n][e] * self.delta_use[n][e][t] + \
									 self.regressor_belowSet_b[n][e] - \
									 self.bigNumber[n][e] * binAux[n][e][t], \
							f'Constraint_8.5_{n}_{e}_{t:07d}'
						self.milp += w_water[n][e][t] <= \
									 self.regressor_belowSet_m_temp[n][e] * temp[n][e][t] + \
									 self.regressor_belowSet_m_delta[n][e] * self.delta_use[n][e][t] + \
									 self.regressor_belowSet_b[n][e] + \
									 self.bigNumber[n][e] * binAux[n][e][t], \
							f'Constraint_8.6_{n}_{e}_{t:07d}'
					else:
						self.milp += w_water[n][e][t] == \
									 temp[n][e][t] * self.ewh_capacity[n][e] * self.waterHeatCap[n][e] / 3600 * \
									 self.delta_t[n][e] * 60, \
							f'Constraint_8.7_{n}_{e}_{t:07d}'

		# HVAC Constraints
		if self.set_hvac is not None:
			for n, t in itertools.product(self.set_meters, self.time_series):
				for h in self.set_hvac[n]:
					increment = f'{n}_{h}_t{t:03d}'

					# Temperature Evolution Equation
					if t == 0:
						self.milp += hvac_temp[n][h][t] == self.hvac_init_temp[n][h], f'HVAC_Start_Temp_' + increment

					if self.type[n][h] == 'inverter':
						if t != 0:
							# Heating equation
							self.milp += (
												 hvac_temp[n][h][t]
												 - hvac_temp[n][h][t - 1]
												 - self.mu[n][h] * (self.T_out[n][h][t] - hvac_temp[n][h][t - 1])
												 - self.psi[n][h] * hvac_power[n][h][t] * self._delta_t
												 <= self._big_m * (1 - hvac_mode[n][h][t])
										 ), f'HVAC_Heating_UB_' + increment
							self.milp += (
												 hvac_temp[n][h][t]
												 - hvac_temp[n][h][t - 1]
												 - self.mu[n][h] * (self.T_out[n][h][t] - hvac_temp[n][h][t - 1])
												 - self.psi[n][h] * hvac_power[n][h][t] * self._delta_t
												 >= -self._big_m * (1 - hvac_mode[n][h][t])
										 ), f'HVAC_Heating_LB_' + increment

							# Cooling equation
							self.milp += (
												 hvac_temp[n][h][t]
												 - hvac_temp[n][h][t - 1]
												 - self.mu[n][h] * (self.T_out[n][h][t] - hvac_temp[n][h][t - 1])
												 + self.psi[n][h] * hvac_power[n][h][t] * self._delta_t
												 <= self._big_m * hvac_mode[n][h][t]
										 ), f'HVAC_Cooling_UB_' + increment
							self.milp += (
												 hvac_temp[n][h][t]
												 - hvac_temp[n][h][t - 1]
												 - self.mu[n][h] * (self.T_out[n][h][t] - hvac_temp[n][h][t - 1])
												 + self.psi[n][h] * hvac_power[n][h][t] * self._delta_t
												 >= -self._big_m * hvac_mode[n][h][t]
										 ), f'HVAC_Cooling_LB_' + increment

						self.milp += delta_hvac[n][h][t] <= 5 * hvac_active[n][h][
							t], f'HVAC_Activation_Control_' + increment
						self.milp += hvac_power[n][h][t] == 0.2 * delta_hvac[n][h][t] * self.hvac_capacity[n][
							h], f'HVAC_Power_Level_' + increment

					if self.type[n][h] == 'state':
						if t != 0:
							self.milp += (hvac_mode_heat[n][h][t] + hvac_mode_off[n][h][t] + hvac_mode_cool[n][h][
								t] == 1), f'HVAC_mode_sum_' + increment
							# Heating mode
							self.milp += (hvac_temp[n][h][t] <= (
									self.T_out[n][h][t] + hvac_power[n][h][t] * self.thermal_resist[n][h] - (
									self.T_out[n][h][t] + hvac_power[n][h][t] * self.thermal_resist[n][h] -
									hvac_temp[n][h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[n][h] * self.thermal_cap[n][h])))
										  + self._big_m * (1 - hvac_mode_heat[n][h][
										t])), f'HVAC_Heating_UB_state' + increment
							self.milp += (hvac_temp[n][h][t] >= (
									self.T_out[n][h][t] + hvac_power[n][h][t] * self.thermal_resist[n][h] - (
									self.T_out[n][h][t] + hvac_power[n][h][t] * self.thermal_resist[n][h] -
									hvac_temp[n][h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[n][h] * self.thermal_cap[n][h])))
										  - self._big_m * (1 - hvac_mode_heat[n][h][
										t])), f'HVAC_Heating_LB_state' + increment

							# off mode
							self.milp += (hvac_temp[n][h][t] <= (
									self.T_out[n][h][t] - (
									self.T_out[n][h][t] -
									hvac_temp[n][h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[n][h] * self.thermal_cap[n][h])))
										  + self._big_m * (
													  1 - hvac_mode_off[n][h][t])), f'HVAC_Off_UB_state' + increment
							self.milp += (hvac_temp[n][h][t] >= (
									self.T_out[n][h][t] - (
									self.T_out[n][h][t] -
									hvac_temp[n][h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[n][h] * self.thermal_cap[n][h])))
										  - self._big_m * (
													  1 - hvac_mode_off[n][h][t])), f'HVAC_Off_LB_state' + increment

							# Cooling mode
							self.milp += (hvac_temp[n][h][t] <= (
									self.T_out[n][h][t] - hvac_power[n][h][t] * self.thermal_resist[n][h] - (
									self.T_out[n][h][t] - hvac_power[n][h][t] * self.thermal_resist[n][h] -
									hvac_temp[n][h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[n][h] * self.thermal_cap[n][h])))
										  + self._big_m * (1 - hvac_mode_heat[n][h][
										t])), f'HVAC_Cooling_UB_state' + increment
							self.milp += (hvac_temp[n][h][t] >= (
									self.T_out[n][h][t] - hvac_power[n][h][t] * self.thermal_resist[n][h] - (
									self.T_out[n][h][t] - hvac_power[n][h][t] * self.thermal_resist[n][h] -
									hvac_temp[n][h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[n][h] * self.thermal_cap[n][h])))
										  - self._big_m * (1 - hvac_mode_heat[n][h][
										t])), f'HVAC_Cooling_LB_state' + increment

						self.milp += hvac_active[n][h][t] == hvac_mode_heat[n][h][t] + hvac_mode_cool[n][h][
							t], f'HVAC_Active_Link_' + increment
						self.milp += hvac_power[n][h][t] == hvac_active[n][h][t] * self.hvac_capacity[n][
							h], f'HVAC_On_Off_' + increment

					# Force HVAC Activation If Temperature Exceeds Limits
					self.milp += hvac_temp[n][h][t] <= self.hvac_temp_max[n][h] + self._big_m * hvac_active[n][h][
						t], f'HVAC_Turn_On_Above_' + increment
					self.milp += hvac_temp[n][h][t] >= self.hvac_temp_min[n][h] - self._big_m * hvac_active[n][h][
						t], f'HVAC_Turn_On_Below_' + increment

					self.milp += hvac_temp[n][h][t] - self.hvac_temp_max[n][h] <= hvac_cost_comfort[n][h][
						t], f'HVAC_Cost_Above_UB' + increment
					self.milp += hvac_temp[n][h][t] - self.hvac_temp_min[n][h] >= -hvac_cost_comfort[n][h][
						t], f'HVAC_Cost_Below_UB' + increment

		if self.set_hp is not None:
			for n, t in itertools.product(self.set_meters, self.time_series):
				for hp in self.set_hp[n]:

					if self.hp_type[n][hp] == 'inverter':

						increment = f'{n}_{hp}_t{t:03d}'

						self.milp += self.hp_power[n][hp][t] <= self.hp_power_rated[n][hp]

						# HPT-2.1
						self.milp += (self.hp_power[n][hp][t] >= self.heating_kwh[n][hp][t] +
									self.circulation_kw[n][hp][t] + self.tank_heating_kwh[n][hp][t]), f'HP_Total_Power_' + increment

						# HPT-2.2
						self.milp += (self.heating_kwh[n][hp][t] >= self.hp_mass_hw_demand[n][hp][t] * self.hp_c_p[n][hp] * (
									self.hp_temp_desired[n][hp] - self.hp_temp_inlet[n][
								hp])/ 3600 * self._delta_t), f'HP_Heating_Demand_' + increment

						# HPT-2.3
						self.milp += (self.circulation_kw[n][hp][t] >= self.hp_mass_radiator[n][hp][t] * self.hp_c_p[n][hp] * (
									self.hp_temp_outlet[n][hp][t] - self.hp_temp_return[n][hp][
								t])/ 3600 * self._delta_t), f'HP_Circulation_Power_' + increment

						# HPT-2.5
						# if t ==0:
						# 	self.milp += (self.tank_heating_kwh[hp][t] == self.hp_capacity_tank[hp] * self.hp_c_p[hp] * self.hp_temp_out_init[hp]/3600), f'HP_Tank_Init_' + increment
						if t != 0:
							# HPT-2.4
							self.milp += (self.tank_heating_kwh[n][hp][t] >= self.hp_capacity_tank[n][hp] * self.hp_c_p[n][hp] * (
									self.hp_temp_outlet[n][hp][t] - self.hp_temp_outlet[n][hp][
								t - 1])/ 3600 * self._delta_t), f'HPT2.4_Tank_Heating_' + increment

						# HPT-3
						# self.milp += self.circulation_kw[hp][t] == ((self.hp_h_rad[hp] * self.hp_area_rad[hp]) * ((self.hp_temp_outlet[hp][t]
						# 										+ self.hp_temp_return[hp][t])/2 - self.hp_temp_indoor[hp][t])), f'HP_Convective_Limit_' + increment

						self.milp += (self.hp_mass_radiator[n][hp][t] * self.hp_c_p[n][hp] * (
								self.hp_temp_outlet[n][hp][t] - self.hp_temp_return[n][hp][t]) / 3600) == (
												(self.hp_h_rad[n][hp] * self.hp_area_rad[n][hp]) * ((self.hp_temp_outlet[n][hp][t]
												+ self.hp_temp_return[n][hp][t]) / 2 - self.hp_temp_indoor[n][hp][t]) * self._delta_t), f'HP_Convective_Limit_' + increment


						# HPT-4.1/ 4.2: Indoor temperature evolution
						if t == 0:
							self.milp += (self.hp_temp_indoor[n][hp][t] == self.hp_temp_indoor_init[n][hp]), f'HP_Indoor_Init_' + increment
							self.milp += (self.hp_temp_outlet[n][hp][t] == self.hp_temp_out_init[n][hp]), f'HP_Outlet_Init_' + increment
						else:
							# self.milp += ( self.hp_temp_indoor[h][t] == self.hp_temp_indoor[h][t - 1]
							# 					+ (self._delta_t / self.hp_thermal_resistance[h]) * self.hp_u_value[h] * (self.hp_t_out[h][t - 1] - self.hp_temp_indoor[h][t - 1])
							# 					+ self.hp_h_rad[h] * self.hp_area_rad[h] * (self.hp_temp_outlet[h][t - 1] - self.hp_temp_indoor[h][t - 1])
							# 			 ), f'HP_Indoor_Evolution_' + increment

							self.milp += (self.hp_temp_indoor[n][hp][t] == self.hp_temp_indoor[n][hp][t - 1] * self.hp_u_value[n][hp] +
										  self.hp_t_out[n][hp][t - 1] * (self._delta_t / self.hp_thermal_resistance[n][hp])
										  + self.hp_h_rad[n][hp] * self.hp_area_rad[n][hp] * self.hp_temp_outlet[n][hp][
											  t]), f'HP_Indoor_Evolution_' + increment

						# HPT-5
						self.milp += (self.hp_temp_indoor[n][hp][t] + self.hp_cost_comfort[n][hp][t] >= self.hp_temp_indoor_min[n][
							hp]), f'HP_Temp_Min_WithSlack_' + increment
						self.milp += (self.hp_temp_indoor[n][hp][t] + self.hp_cost_comfort[n][hp][t] <= self.hp_temp_indoor_max[n][
							hp]), f'HP_Temp_Max_WithSlack_' + increment
						# HPT-5
						# self.milp += (self.hp_temp_outlet[n][hp][t] + self.hp_cost_comfort[n][hp][t] >= self.hp_temp_out_min[n][
						# 	hp]), f'HP_TempOut_Min_WithSlack_' + increment
						# self.milp += (self.hp_temp_outlet[n][hp][t] + self.hp_cost_comfort[n][hp][t] <= self.hp_temp_out_max[n][
						# 	hp]), f'HP_TempOut_Max_WithSlack_' + increment

		# Write MILP to .lp file
		dir_name = os.path.abspath(os.path.join(__file__, '..'))
		lp_file = os.path.join(dir_name, f'Stage2Bilateral.lp')
		self.milp.writeLP(lp_file)

		# Set the solver to be called
		if self.solver == 'CBC' and 'PULP_CBC_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(pulp.PULP_CBC_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap))

		elif self.solver == 'GUROBI' and 'GUROBI_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(GUROBI_CMD(msg=False, timeLimit=self.timeout, mip=self.mipgap))

		elif self.solver == 'CPLEX' and 'CPLEX_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(CPLEX_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap))

		elif self.solver == 'HiGHS' and 'HiGHS_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(HiGHS_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap, threads=1))

		else:
			raise ValueError(f'{self.solver}_CMD not available in puLP; '
							 f'please install the required solver or try a different one')

		logger.debug('-- defining the collective (bilateral) MILP problem... DONE!')

		return

	def solve_milp(self):
		"""
		Function that heads the definition and solution of the second stage MILP.
		"""
		# Define the MILP
		self.__define_milp()

		# Solve the MILP
		logger.debug('-- solving the collective (bilateral) MILP problem...')

		try:
			self.milp.solve()
			status = LpStatus[self.milp.status]
			opt_value = value(self.milp.objective)

		except Exception as e:
			logger.warning(f'Solver raised an error: \'{e}\'. Considering problem as "Infeasible".')
			status = 'Infeasible'
			opt_value = None

		self.status = status
		self.obj_value = opt_value

		logger.debug('-- solving the collective (bilateral) MILP problem... DONE!')

		return

	def generate_outputs(self) -> OutputsS2BilateralDict:
		"""
		Function for generating the outputs of optimization, namely the battery's set points.
		:return: outputs dictionary with MILP variables' and other computed values
		"""
		logger.debug('-- generating outputs from the collective (bilateral) MILP problem...')

		outputs = {}

		# -- Verification added to avoid raising error whenever encountering a puLP solver error with CBC
		if self.obj_value is None:
			return outputs

		outputs['obj_value'] = self.obj_value
		outputs['milp_status'] = self.status

		outputs['e_sup_retail'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_sur_retail'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_sup_market'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_sur_market'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['delta_sup'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_pur_bilateral'] = \
			{n: dict_none_lists(self.time_intervals, self.sets_other_meters[n]) for n in self.set_meters}
		outputs['e_sale_bilateral'] = \
			{n: dict_none_lists(self.time_intervals, self.sets_other_meters[n]) for n in self.set_meters}
		outputs['e_cmet'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_slc_bilateral'] = \
			{n: dict_none_lists(self.time_intervals, self.sets_other_meters[n]) for n in self.set_meters}
		outputs['e_consumed'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_alc'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['delta_slc'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['delta_cmet'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['delta_alc'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['p_extra'] = dict_none_lists(self.time_intervals, self.set_meters)
		outputs['e_bat'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		outputs['soc_bat'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		outputs['e_bc'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		outputs['e_bd'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		outputs['delta_bc'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_storage[n]) for n in self.set_meters}
		for n_meter in self.set_meters:
			meter_btm_ev = self._meters_data[n_meter].get('btm_evs') #Check if there are EVs
			if meter_btm_ev is not None:
				outputs['ev_stored'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_ev[n]) for n in self.set_meters}
				outputs['p_ev_charge'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_ev[n]) for n in self.set_meters}
				outputs['p_ev_discharge'] = {n: dict_none_lists(self.time_intervals, self.sets_btm_ev[n]) for n in self.set_meters}
				break
		if self.strict_pos_coeffs:
			outputs['delta_coeff'] = dict_none_lists(self.time_intervals, self.set_meters)
		if self.total_share_coeffs:
			outputs['delta_rec_balance'] = none_lists(self.time_intervals)
			outputs['delta_meter_balance'] = dict_none_lists(self.time_intervals, self.set_meters)

		# Required when vars include "-" since puLP converts it to "_"
		btm_storage_ids = [bid for bids in [v for _, v in self.sets_btm_storage.items()] for bid in bids]
		matchd = {key: key.replace('-', '_') for key in self.set_meters}
		b_matchd = {key: key.replace('-', '_') for key in btm_storage_ids}

		# Auxiliary lambda functions to extract the neter and batteries' designations from the variables
		original_n_name = \
			lambda v_name: [ori_n for ori_n in self.set_meters if matchd[ori_n] + '_' in v_name][0]
		original_b_name = \
			lambda v_name: [ori_b for ori_b in btm_storage_ids if b_matchd[ori_b] + '_' in v_name][0]
		alt_original_n_name = \
			lambda v_name, v_group: [ori_n for ori_n in self.set_meters if v_group + matchd[ori_n] in v.name][0]
		original_m_name = \
			lambda v_name, v_group: [ori_m for ori_m in self.set_meters if (matchd[ori_m] in v_name) and
									 (matchd[ori_m] != matchd[alt_original_n_name(v_name, v_group)])][0]

		# EVs______________________________________________________________________________________________
		# Required when vars include "-" since puLP converts it to "_"
		btm_ev_ids = [bid for bids in [v for _, v in self.sets_btm_ev.items()] for bid in bids]
		matchd = {key: key.replace('-', '_') for key in self.set_meters}
		ev_matchd = {key: key.replace('-', '_') for key in btm_ev_ids}

		original_ev_name = \
			lambda v_name: [ori_ev for ori_ev in btm_ev_ids if ev_matchd[ori_ev] + '_' in v_name][0]
		# EVs______________________________________________________________________________________________

		# required when vars include "-" since puLP converts it to "_"
		matchd = {key: key.replace('-', '_') for key in self.set_meters}
		rematchd = {v: k for k, v in matchd.items()}
		var_name = lambda v_str, n_str: rematchd[v_str.split(n_str)[-1]]

		# EWH outputs
		if bool(self._ewh_dataset):
			outputs['ewh_temp'] = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in self.set_meters}
			outputs['ewh_delta_in'] = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in
									   self.set_meters}
			outputs['ewh_optimized_load'] = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in
											 self.set_meters}
			outputs['ewh_original_load'] = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in
											self.set_meters}
			outputs['ewh_delta_use'] = {n: dict_none_lists(self.time_intervals, self.set_ewh[n]) for n in
										self.set_meters}

			ewh_ids = [bid for bids in [v for _, v in self.set_ewh.items()] for bid in bids]
			e_matchd = {key: key.replace('-', '_') for key in ewh_ids}
			original_e_name = lambda v_name: [ori_e for ori_e in ewh_ids if e_matchd[ori_e] + '_' in v_name][0]
			original_n_name = lambda v_name: [ori_n for ori_n in self.set_meters if matchd[ori_n] + '_' in v_name][0]

		# HVAC outputs
		if not all(isinstance(v, list) and not v for v in self.set_hvac.values()):
			outputs['hvac_power'] = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}
			outputs['hvac_temp'] = {n: dict_none_lists(self.time_intervals, self.set_hvac[n]) for n in self.set_meters}

			hvac_ids = [bid for bids in [v for _, v in self.set_hvac.items()] for bid in bids]
			h_matchd = {key: key.replace('-', '_') for key in hvac_ids}
			original_h_name = lambda v_name: [ori_h for ori_h in hvac_ids if h_matchd[ori_h] + '_' in v_name][0]

		# HP outputs
		if not all(isinstance(v, list) and not v for v in self.set_hp.values()):
			outputs['hp_power'] = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in
								   self.set_meters}
			outputs['hp_temp_indoor'] = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in
										 self.set_meters}
			outputs['hp_power_circulation'] = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in
											   self.set_meters}
			outputs['hp_power_heating'] = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in
										   self.set_meters}
			outputs['hp_power_tank'] = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in
										self.set_meters}
			outputs['hp_outlet_temp'] = {n: dict_none_lists(self.time_intervals, self.set_hp[n]) for n in
										 self.set_meters}
			hp_ids = [bid for bids in [v for _, v in self.set_hp.items()] for bid in bids]
			hp_matchd = {key: key.replace('-', '_') for key in hp_ids}
			original_hp_name = lambda v_name: [ori_hp for ori_hp in hp_ids if hp_matchd[ori_hp] + '_' in v_name][0]

		# Associate the values of the variables with the respective outputs' structure
		for v in self.milp.variables():
			if re.search('dummy', v.name):
				continue

			# Returns the variable name termination "t000"
			step_nr = int(v.name[-3:])

			if re.search(f'e_sup_retail_', v.name):
				n = original_n_name(v.name)
				outputs['e_sup_retail'][n][step_nr] = v.varValue
			elif re.search(f'e_sur_retail_', v.name):
				n = original_n_name(v.name)
				outputs['e_sur_retail'][n][step_nr] = v.varValue
			elif re.search(f'e_sup_market_', v.name):
				n = original_n_name(v.name)
				outputs['e_sup_market'][n][step_nr] = v.varValue
			elif re.search(f'e_sur_market_', v.name):
				n = original_n_name(v.name)
				outputs['e_sur_market'][n][step_nr] = v.varValue
			elif re.search(f'delta_sup_', v.name):
				n = original_n_name(v.name)
				outputs['delta_sup'][n][step_nr] = v.varValue
			elif re.search(f'e_pur_', v.name):
				n = alt_original_n_name(v.name, 'e_pur_')
				m = original_m_name(v.name, 'e_pur_')
				outputs['e_pur_bilateral'][n][m][step_nr] = v.varValue
			elif re.search(f'e_sale_', v.name):
				n = alt_original_n_name(v.name, 'e_sale_')
				m = original_m_name(v.name, 'e_sale_')
				outputs['e_sale_bilateral'][n][m][step_nr] = v.varValue
			elif re.search(f'e_cmet_', v.name):
				n = original_n_name(v.name)
				outputs['e_cmet'][n][step_nr] = v.varValue
			elif re.search(f'e_slc_', v.name):
				n = alt_original_n_name(v.name, 'e_slc_')
				m = original_m_name(v.name, 'e_slc_')
				outputs['e_slc_bilateral'][n][m][step_nr] = v.varValue
			elif re.search(f'e_consumed_', v.name):
				n = original_n_name(v.name)
				outputs['e_consumed'][n][step_nr] = v.varValue
			elif re.search(f'e_alc_', v.name):
				n = original_n_name(v.name)
				outputs['e_alc'][n][step_nr] = v.varValue
			elif re.search(f'delta_slc_', v.name):
				n = original_n_name(v.name)
				outputs['delta_slc'][n][step_nr] = v.varValue
			elif re.search(f'delta_cmet_', v.name):
				n = original_n_name(v.name)
				outputs['delta_cmet'][n][step_nr] = v.varValue
			elif re.search(f'delta_alc_', v.name):
				n = original_n_name(v.name)
				outputs['delta_alc'][n][step_nr] = v.varValue
			elif re.search(f'delta_coeff_', v.name):
				n = original_n_name(v.name)
				outputs['delta_coeff'][n][step_nr] = v.varValue
			elif re.search(f'delta_meter_balance_', v.name):
				n = original_n_name(v.name)
				outputs['delta_meter_balance'][n][step_nr] = v.varValue
			elif re.search(f'p_extra_', v.name):
				n = original_n_name(v.name)
				outputs['p_extra'][n][step_nr] = v.varValue
			elif re.search(f'e_bat_', v.name):
				n = original_n_name(v.name)
				b = original_b_name(v.name)
				outputs['e_bat'][n][b][step_nr] = v.varValue
			elif re.search(f'soc_bat_', v.name):
				n = original_n_name(v.name)
				b = original_b_name(v.name)
				outputs['soc_bat'][n][b][step_nr] = v.varValue
			elif re.search(f'e_bc_', v.name):
				n = original_n_name(v.name)
				b = original_b_name(v.name)
				outputs['e_bc'][n][b][step_nr] = v.varValue
			elif re.search(f'e_bd_', v.name):
				n = original_n_name(v.name)
				b = original_b_name(v.name)
				outputs['e_bd'][n][b][step_nr] = v.varValue
			elif re.search(f'delta_bc_', v.name):
				n = original_n_name(v.name)
				b = original_b_name(v.name)
				outputs['delta_bc'][n][b][step_nr] = v.varValue
			# EVs
			elif re.search(f'ev_stored_', v.name):
				n = original_n_name(v.name)
				ev = original_ev_name(v.name)
				outputs['ev_stored'][n][ev][step_nr] = v.varValue
			elif re.search(f'p_ev_charge_', v.name):
				n = original_n_name(v.name)
				ev = original_ev_name(v.name)
				outputs['p_ev_charge'][n][ev][step_nr] = v.varValue
			elif re.search(f'p_ev_discharge_', v.name):
				n = original_n_name(v.name)
				ev = original_ev_name(v.name)
				outputs['p_ev_discharge'][n][ev][step_nr] = v.varValue
			# EWH outputs
			elif v.name.startswith('temp_') and not v.name.startswith(('hvac_temp_', 'hp_temp_indoor_')):
				n = original_n_name(v.name)
				e = original_e_name(v.name)
				outputs['ewh_temp'][n][e][step_nr] = v.varValue
			elif re.search(f'delta_in_', v.name):
				n = original_n_name(v.name)
				e = original_e_name(v.name)
				outputs['ewh_delta_in'][n][e][step_nr] = v.varValue
				outputs['ewh_optimized_load'][n][e][step_nr] = v.varValue * varBackpack[n][e]['ewh_power']
				outputs['ewh_original_load'][n][e] = varBackpack[n][e]['original_load']
				outputs['ewh_delta_use'][n][e] = varBackpack[n][e]['delta_use']
			# HVAC
			elif re.search(f'hvac_power_', v.name):
				n = original_n_name(v.name)
				h = original_h_name(v.name)
				outputs['hvac_power'][n][h][step_nr] = v.varValue
			elif re.search(f'hvac_temp_', v.name):
				n = original_n_name(v.name)
				h = original_h_name(v.name)
				outputs['hvac_temp'][n][h][step_nr] = v.varValue

				# HP
			elif re.search(f'power_hp_', v.name):
				n = original_n_name(v.name)
				hp = original_hp_name(v.name)
				outputs['hp_power'][n][hp][step_nr] = v.varValue
			elif re.search(f'hp_temp_indoor_', v.name):
				n = original_n_name(v.name)
				hp = original_hp_name(v.name)
				outputs['hp_temp_indoor'][n][hp][step_nr] = v.varValue
			elif re.search(f'hp_power_heating_', v.name):
				n = original_n_name(v.name)
				hp = original_hp_name(v.name)
				outputs['hp_power_heating'][n][hp][step_nr] = v.varValue
			elif re.search(f'hp_power_circulation_', v.name):
				n = original_n_name(v.name)
				hp = original_hp_name(v.name)
				outputs['hp_power_circulation'][n][hp][step_nr] = v.varValue
			elif re.search(f'hp_power_tank_', v.name):
				n = original_n_name(v.name)
				hp = original_hp_name(v.name)
				outputs['hp_power_tank'][n][hp][step_nr] = v.varValue
			elif re.search(f'hp_temp_outlet_', v.name):
				n = original_n_name(v.name)
				hp = original_hp_name(v.name)
				outputs['hp_outlet_temp'][n][hp][step_nr] = v.varValue

		# Include other individual cost metrics
		outputs['c_ind2bilateral'] = {n: None for n in self.set_meters}
		outputs['c_ind2bilateral_without_deg'] = {n: None for n in self.set_meters}
		outputs['c_ind2bilateral_without_deg_and_p_extra'] = {n: None for n in self.set_meters}
		outputs['c_ind2bilateral_without_p_extra'] = {n: None for n in self.set_meters}
		outputs['deg_cost2bilateral'] = {n: None for n in self.set_meters}
		outputs['p_extra_cost2bilateral'] = {n: None for n in self.set_meters}

		# Calculate the individual costs found on stage 2
		rematchd = {v: k for k, v in matchd.items()}
		constraints = [self.milp.constraints[c] for c in self.milp.constraints if c.startswith('Stage_1_cost_')]
		for constraint in constraints:
			# Calculate the cost that came from overstepping the maximum Meter power limit
			n = rematchd[constraint.name.split('Stage_1_cost_')[-1]]
			p_extra = sum(outputs['p_extra'][n])
			p_extra_cost = p_extra * self._l_extra
			outputs['p_extra_cost2bilateral'][n] = p_extra_cost

			# Calculate the cost of degradation
			deg_cost = 0
			for b, t in itertools.product(self.sets_btm_storage[n], self.time_series):
				deg_cost += self._deg_cost[n][b] * outputs['e_bd'][n][b][t]
			outputs['deg_cost2bilateral'][n] = deg_cost

			# Retrieve the cost with energy of each Meter obtained in Stage 2
			constraint_sum = 0
			for var, coefficient in constraint.items():
				constraint_sum += var.varValue * coefficient
			constraint_sum += constraint.constant + self._c_ind[n]
			outputs['c_ind2bilateral'][n] = constraint_sum

			# Calculate additional terms that do not consider the cost of degradation and/or extra power at Meter:
			outputs['c_ind2bilateral_without_deg'][n] = (
					outputs['c_ind2bilateral'][n] - deg_cost)
			outputs['c_ind2bilateral_without_p_extra'][n] = (
					outputs['c_ind2bilateral'][n] - p_extra_cost)
			outputs['c_ind2bilateral_without_deg_and_p_extra'][n] = (
					outputs['c_ind2bilateral'][n] - deg_cost - p_extra_cost)

		logger.debug('-- generating outputs from the collective (bilateral) MILP problem... DONE!')

		return outputs


if __name__ == '__main__':
	from rec_op_lem_prices.optimization.structures.I_O_stage_2_bilateral_milp import (
		INPUTS_S2_BILATERAL,
		OUTPUTS_S2_BILATERAL
	)

	# Assert the creation of a correct class
	milp = StageTwoMILPBilateral(INPUTS_S2_BILATERAL)
	assert isinstance(milp, StageTwoMILPBilateral)

	# Assert the MILP is optimally solved
	milp.solve_milp()
	assert milp.status == 'Optimal'

	# Assert the correct outputs
	results = milp.generate_outputs()
	round_cost = lambda x: {meter_id: round(cost, 3) for meter_id, cost in x.items()}
	results['obj_value'] = round(results['obj_value'], 3)
	results['c_ind2bilateral'] = round_cost(results['c_ind2bilateral'])
	results['c_ind2bilateral_without_deg'] = round_cost(results['c_ind2bilateral_without_deg'])
	results['c_ind2bilateral_without_deg_and_p_extra'] = round_cost(results['c_ind2bilateral_without_deg_and_p_extra'])
	results['c_ind2bilateral_without_p_extra'] = round_cost(results['c_ind2bilateral_without_p_extra'])
	for ki, valu in results.items():
		assert valu == OUTPUTS_S2_BILATERAL.get(ki), f'{ki}'
