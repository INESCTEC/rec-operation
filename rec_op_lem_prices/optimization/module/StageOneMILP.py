"""
Class for implementing and running the Stage 1 MILP for each individual Meter / microgrid / hybrid park.
"""
import itertools
import math
import os
import re

from rec_op_lem_prices.configs.configs import (
	MIPGAP,
	SOLVER,
	TIMEOUT
)
from rec_op_lem_prices.optimization.helpers.milp_helpers import (
	dict_none_lists,
	none_lists,
	time_intervals
)
from rec_op_lem_prices.custom_types.stage_one_milp_types import (
	BackpackS1Dict,
	OutputsS1Dict
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
from math import exp


class StageOneMILP:
	def __init__(self, backpack: BackpackS1Dict, solver=SOLVER, timeout=TIMEOUT, mipgap=MIPGAP):
		# Indices and sets
		self._horizon = backpack.get('horizon')  # operation period [h]
		# Parameters
		self._delta_t = backpack.get('delta_t')  # interval settlement duration [h]
		self._l_buy = backpack.get('l_buy')  # supply energy tariff [€/kWh]
		self._l_sell = backpack.get('l_sell')  # feed in energy tariff [€/kWh]
		self._l_market_buy = backpack.get('l_market_buy')  # market-indexed buying tariff [€/kWh]
		self._l_market_sell = backpack.get('l_market_sell')  # market-indexed selling tariff [€/kWh]
		self._e_c = backpack.get('e_c')  # Meter load profile [kWh]
		self._e_g = backpack.get('e_g')  # Meter generation [kWh]
		self._p_meter_max = backpack.get('max_p')  # Maximum power flow desired at the Meter [kW]
		self._btm_storage = backpack.get('btm_storage')  # Btm storage parameters
		self._btm_ev = backpack.get('btm_evs') # Btm evs parameters
		self._trip_ev = {} #EV energy consumption, in kWh
		self._min_energy_storage_ev = {} # Minimum stored energy to be guaranteed for vehicle ev at CPE n, in kWh
		self._battery_capacity_ev = {} # The battery energy capacity of vehicle ev at CPE n, in kWh
		self._eff_bc_ev = {} # Charging efficiency of vehicle ev at CPE n, between 0 and 1
		self._eff_bd_ev = {} # Discharging efficiency of vehicle ev at CPE n, between 0 and 1
		self._init_e_ev = {} # the initial energy content of the EV, in kWh
		self._pmax_c_ev = {} # Maximum power charge of vehicle ev at CPE n, in kW
		self._pmax_d_ev = {} # Maximum power discharge of vehicle ev at CPE n, in kW
		self._bin_ev = {} # Whether a vehicle ev at CPE n is plugged-in or not (if plugged-in = 1 else = 0)
		self._eff_bc = {}  # charging efficiency of the batteries [%]
		self._eff_bd = {}  # discharging efficiency of the batteries [%]
		self._p_max = {}  # maximum input and output batteries' power [kW]
		self._e_bn = {}  # nominal capacity of the batteries of n [kWh]
		self._soc_min = {}  # minimum state of charge [%]
		self._soc_max = {}  # maximum state of charge [%]
		self._init_e_bat = {}  # initial energy content of the batteries [kWh]
		self._deg_cost = {}  # estimated degradation cost of the batteries of n [€/kWh]
		self._big_m = 10 * self._p_meter_max  # a very big number [kWh]
		self._l_extra = backpack.get('l_extra')  # (fictitious) very high cost of violating p_meter_max
		# MILP variables
		self.milp = None  # for storing the MILP formulation
		self.solver = solver  # solver chosen for the MILP
		self.timeout = timeout  # solvers temporal limit to find optimal solution (s)
		self.mipgap = mipgap  # controls the solver's tolerance; intolerant [0 - 1] fully permissive
		self.status = None  # stores the status of the MILP's solution
		self.obj_value = None  # stores the MILP's numeric solution
		self.meter_id = backpack.get('id')  # identification of the Meter for which te MILP will run
		self.time_intervals = None  # for number of time intervals per horizon
		self.time_series = None  # for a range of time intervals
		self.set_btm_storage = [] # stores the Meter's Btm storage assets' ids
		self.set_btm_evs = [] # stores the evs' ids
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
		try:
			self._ewh = backpack.get('ewh') # NEW EW
		except:
			self._ewh = None
		# HVAC
		self._hvac = backpack.get('hvac')
		self.mu = {}  # Building insulation factor
		self.psi = {}  # HVAC temperature efficiency factor
		self.hvac_temp_min = {}  # Min room temperature constraint
		self.hvac_temp_max = {}  # Max room temperature constraint
		self.hvac_init_temp = {}  # Initial room temperature
		self.hvac_capacity = {}  # Maximum HVAC power
		self.T_out = {} # Outside temperature
		self.thermal_resist= {}
		self.thermal_cap = {}
		self.type= {}
		self.set_hvac = []  # Set of active HVAC units
		# HP
		self._hp = backpack.get('hp')
		self.set_hp = []


	def __define_milp(self):
		"""
		Method to define the first stage MILP problem.
		"""
		logger.debug(f'-- defining the individual MILP problem for Meter id: {self.meter_id}...')
		# Define a minimization MILP
		n = self.meter_id
		self.milp = LpProblem(f'stage1_{n}', LpMinimize)

		# Additional temporal variables
		self.time_intervals = time_intervals(self._horizon, self._delta_t)
		self.time_series = range(self.time_intervals)

		#Unpack EVs information
		if self._btm_ev is not None:
			self.set_btm_evs = list(self._btm_ev.keys())
		self._trip_ev = {ev: self._btm_ev[ev]['trip_ev'] for ev in self.set_btm_evs}
		self._min_energy_storage_ev = {ev: self._btm_ev[ev]['min_energy_storage_ev'] for ev in self.set_btm_evs}
		self._battery_capacity_ev = {ev: self._btm_ev[ev]['battery_capacity_ev'] for ev in self.set_btm_evs}
		self._eff_bc_ev = {ev: self._btm_ev[ev]['eff_bc_ev'] for ev in self.set_btm_evs}
		self._eff_bd_ev = {ev: self._btm_ev[ev]['eff_bd_ev'] for ev in self.set_btm_evs}
		self._init_e_ev = {ev: self._btm_ev[ev]['init_e_ev'] for ev in self.set_btm_evs}
		self._pmax_c_ev = {ev: self._btm_ev[ev]['pmax_c_ev'] for ev in self.set_btm_evs}
		self._pmax_d_ev = {ev: self._btm_ev[ev]['pmax_d_ev'] for ev in self.set_btm_evs}
		self._bin_ev = {ev: self._btm_ev[ev]['bin_ev'] for ev in self.set_btm_evs}

		# Unpack batteries information
		if self._btm_storage is not None:
			self.set_btm_storage = list(self._btm_storage.keys())
		self._eff_bc = {b: self._btm_storage[b]['eff_bc'] for b in self.set_btm_storage}
		self._eff_bd = {b: self._btm_storage[b]['eff_bd'] for b in self.set_btm_storage}
		self._p_max = {b: self._btm_storage[b]['p_max'] for b in self.set_btm_storage}
		self._e_bn = {b: self._btm_storage[b]['e_bn'] for b in self.set_btm_storage}
		self._soc_min = {b: self._btm_storage[b]['soc_min'] for b in self.set_btm_storage}
		self._soc_max = {b: self._btm_storage[b]['soc_max'] for b in self.set_btm_storage}
		self._init_e_bat = {b: self._btm_storage[b]['init_e'] for b in self.set_btm_storage}
		self._deg_cost = {b: self._btm_storage[b]['degradation_cost'] for b in self.set_btm_storage}

		# Unpack EWH information
		if self._ewh is not None:
			self.set_ewh = list(self._ewh.keys())
			self._ewh_paramsInput = {e: self._ewh[e]['params_input'] for e in self.set_ewh}
			self._ewh_dataset = {e: self._ewh[e]['dataset'] for e in self.set_ewh}

			# create EWH varBackpacks
			from rec_op_lem_prices.ewh.ewh_flex import ewh_preparation
			global varBackpack
			varBackpack = {e: ewh_preparation(self._ewh_paramsInput[e], self._ewh_dataset[e], resample='1h') for e in self.set_ewh}

			self.wh_init = {e: varBackpack[e]['wh_init'] for e in self.set_ewh}
			self.ewh_power = {e: varBackpack[e]['ewh_power'] for e in self.set_ewh}
			self.delta_t = {e: varBackpack[e]['delta_t'] for e in self.set_ewh}
			self.ewh_start_temp = {e: varBackpack[e]['ewh_start_temp'] for e in self.set_ewh}
			self.ewh_capacity = {e: varBackpack[e]['ewh_capacity'] for e in self.set_ewh}
			self.waterHeatCap = {e: varBackpack[e]['waterHeatCap'] for e in self.set_ewh}
			self.heatTransferCoeff = {e: varBackpack[e]['heatTransferCoeff'] for e in self.set_ewh}
			self.ewh_area = {e: varBackpack[e]['ewh_area'] for e in self.set_ewh}
			self.ambTemp = {e: varBackpack[e]['ambTemp'] for e in self.set_ewh}
			self.wh_min = {e: varBackpack[e]['wh_min'] for e in self.set_ewh}
			self.wh_max = {e: varBackpack[e]['wh_max'] for e in self.set_ewh}
			self.ewh_min_temp = {e: varBackpack[e]['ewh_min_temp'] for e in self.set_ewh}
			self.ewh_max_temp = {e: varBackpack[e]['ewh_max_temp'] for e in self.set_ewh}
			self.delta_use = {e: varBackpack[e]['delta_use'] for e in self.set_ewh}
			self.tempSet = {e: varBackpack[e]['tempSet'] for e in self.set_ewh}
			self.bigNumber = {e: varBackpack[e]['bigNumber'] for e in self.set_ewh}
			self.regressor_aboveSet_m_temp = {e: varBackpack[e]['regressor_aboveSet_m_temp'] for e in self.set_ewh}
			self.regressor_aboveSet_m_delta = {e: varBackpack[e]['regressor_aboveSet_m_delta'] for e in self.set_ewh}
			self.regressor_aboveSet_b = {e: varBackpack[e]['regressor_aboveSet_b'] for e in self.set_ewh}
			self.regressor_belowSet_m_temp = {e: varBackpack[e]['regressor_belowSet_m_temp'] for e in self.set_ewh}
			self.regressor_belowSet_m_delta = {e: varBackpack[e]['regressor_belowSet_m_delta'] for e in self.set_ewh}
			self.regressor_belowSet_b = {e: varBackpack[e]['regressor_belowSet_b'] for e in self.set_ewh}

		# Unpack HVAC information
		if self._hvac is not None:
			self.set_hvac = list(self._hvac.keys())
			self.mu = {h: self._hvac[h]['mu'] for h in self.set_hvac}
			self.psi = {h: self._hvac[h]['psi'] for h in self.set_hvac}
			self.hvac_capacity = {h: self._hvac[h]['hvac_capacity'] for h in self.set_hvac}
			self.hvac_temp_min = {h: self._hvac[h]['temp_min'] for h in self.set_hvac}
			self.hvac_temp_max = {h: self._hvac[h]['temp_max'] for h in self.set_hvac}
			self.hvac_init_temp = {h: self._hvac[h]['init_temp'] for h in self.set_hvac}
			self.T_out = {h: self._hvac[h]['t_out'] for h in self.set_hvac}
			self.thermal_resist= {h: self._hvac[h]['thermal_resist'] for h in self.set_hvac}
			self.thermal_cap = {h: self._hvac[h]['thermal_cap'] for h in self.set_hvac}
			self.type = {h: self._hvac[h]['type'] for h in self.set_hvac}

		# Unpack HP information
		if self._hp is not None:
			self.set_hp = list(self._hp.keys())
			self.hp_type = {h: self._hp[h]['type'] for h in self.set_hp}
			self.hp_power_rated = {h: self._hp[h]['power_rated'] for h in self.set_hp}
			self.hp_capacity_tank = {h: self._hp[h]['capacity_tank'] for h in self.set_hp}
			self.hp_c_p = {h: self._hp[h]['c_p'] for h in self.set_hp}
			self.hp_temp_inlet = {h: self._hp[h]['temp_inlet'] for h in self.set_hp}
			self.hp_temp_desired = {h: self._hp[h]['temp_desired'] for h in self.set_hp}
			self.hp_temp_out_init = {h: self._hp[h]['temp_out_init'] for h in self.set_hp}
			self.hp_temp_indoor_init = {h: self._hp[h]['temp_indoor_init'] for h in self.set_hp}
			self.hp_temp_indoor_final = {h: self._hp[h]['temp_indoor_final'] for h in self.set_hp}
			self.hp_temp_indoor_min = {h: self._hp[h]['temp_indoor_min'] for h in self.set_hp}
			self.hp_temp_indoor_max = {h: self._hp[h]['temp_indoor_max'] for h in self.set_hp}
			self.hp_temp_out_min = {h: self._hp[h]['temp_out_min'] for h in self.set_hp}
			self.hp_temp_out_max = {h: self._hp[h]['temp_out_max'] for h in self.set_hp}
			self.hp_u_value = {h: self._hp[h]['u_value'] for h in self.set_hp}
			self.hp_thermal_resistance = {h: self._hp[h]['thermal_resistance'] for h in self.set_hp}
			self.hp_h_rad = {h: self._hp[h]['h_rad'] for h in self.set_hp}
			self.hp_area_rad = {h: self._hp[h]['area_rad'] for h in self.set_hp}
			self.hp_mass_hw_demand = {h: self._hp[h]['mass_hw_demand'] for h in self.set_hp}
			self.hp_mass_radiator = {h: self._hp[h]['mass_radiator'] for h in self.set_hp}
			self.hp_t_out = {h: self._hp[h]['t_out'] for h in self.set_hp}



		# Initialize the decision variables
		e_sup_retail = none_lists(self.time_intervals)  # energy supplied to n from its retailer [kWh]
		e_sur_retail = none_lists(self.time_intervals)  # energy surplus sold by n to its retailer [kWh]
		e_sup_market = none_lists(self.time_intervals)  # energy supplied to n at a market-indexed price [kWh]
		e_sur_market = none_lists(self.time_intervals)  # energy surplus sold by n at a market-indexed price [kWh]
		delta_sup = none_lists(self.time_intervals)  # when True allows supply when false allows surplus
		e_cmet = none_lists(self.time_intervals)  # net consumption at meter n [kWh]
		p_extra = none_lists(self.time_intervals)  # extra power flow at n, beyond p_meter_max [kW]
		e_bat = dict_none_lists(self.time_intervals, self.set_btm_storage)  # energy stored by the batteries of n [kWh]
		soc_bat = dict_none_lists(self.time_intervals, self.set_btm_storage)  # SOC of the batteries of n [%]
		e_bc = dict_none_lists(self.time_intervals, self.set_btm_storage)  # energy charged by n's batteries [kWh]
		e_bd = dict_none_lists(self.time_intervals, self.set_btm_storage)  # energy discharged by n's batteries [kWh]
		delta_bc = dict_none_lists(self.time_intervals, self.set_btm_storage)  # when True allows charge, else discharge
		ev_stored = dict_none_lists(self.time_intervals, self.set_btm_evs) # energy stored in ev at period t
		p_ev_charge = dict_none_lists(self.time_intervals, self.set_btm_evs) # power charge of ev at period t
		p_ev_discharge = dict_none_lists(self.time_intervals, self.set_btm_evs)  # power discharge of ev at period t

		# EWH - Initialize decision variables
		if bool(self._ewh_dataset):
			temp = dict_none_lists(self.time_intervals, self.set_ewh)
			w_tot = dict_none_lists(self.time_intervals, self.set_ewh)
			w_in = dict_none_lists(self.time_intervals, self.set_ewh)
			w_loss = dict_none_lists(self.time_intervals, self.set_ewh)
			delta_in = dict_none_lists(self.time_intervals, self.set_ewh)
			w_water = dict_none_lists(self.time_intervals, self.set_ewh)
			costComfort = dict_none_lists(self.time_intervals, self.set_ewh)
			binAux = dict_none_lists(self.time_intervals, self.set_ewh)
			energyEWH = dict_none_lists(self.time_intervals, self.set_ewh)

		# HVAC - Initialize decision variables
		if self._hvac is not None:
			self.hvac_temp = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_power = dict_none_lists(self.time_intervals, self.set_hvac)
			self.delta_hvac = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_active = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_aux = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_mode = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_cost_comfort = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_mode_heat = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_mode_off = dict_none_lists(self.time_intervals, self.set_hvac)
			self.hvac_mode_cool = dict_none_lists(self.time_intervals, self.set_hvac)

		# HP - Initialize decision variables
		if self._hp is not None:
			self.hp_temp_indoor = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_temp_outlet = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_power = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_active = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_cost_comfort = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_op_mode = dict_none_lists(self.time_intervals, self.set_hp)
			self.heating_kwh = dict_none_lists(self.time_intervals, self.set_hp)
			self.circulation_kw = dict_none_lists(self.time_intervals, self.set_hp)
			self.tank_heating_kwh = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_temp_return = dict_none_lists(self.time_intervals, self.set_hp)
			self.hp_lost_power = dict_none_lists(self.time_intervals, self.set_hp)

		# Define the decision variables as puLP objets
		for t in self.time_series:
			increment = f'{t:03d}'
			e_sup_retail[t] = LpVariable('e_sup_retail_' + increment, lowBound=0)
			e_sur_retail[t] = LpVariable('e_sur_retail_' + increment, lowBound=0)
			e_sup_market[t] = LpVariable('e_sup_market_' + increment, lowBound=0)
			e_sur_market[t] = LpVariable('e_sur_market_' + increment, lowBound=0)
			delta_sup[t] = LpVariable('delta_sup_' + increment, cat=LpBinary)
			e_cmet[t] = LpVariable('e_cmet_' + increment)
			p_extra[t] = LpVariable('p_extra_' + increment, lowBound=0)
			for b in self.set_btm_storage:
				increment = f'{b}_t{t:03d}'
				e_bat[b][t] = LpVariable('e_bat_' + increment, lowBound=0)
				soc_bat[b][t] = LpVariable('soc_bat_' + increment, lowBound=0)
				e_bc[b][t] = LpVariable('e_bc_' + increment, lowBound=0)
				e_bd[b][t] = LpVariable('e_bd_' + increment, lowBound=0)
				delta_bc[b][t] = LpVariable('delta_bc_' + increment, cat=LpBinary)
			for ev in self.set_btm_evs:
				increment = f'{ev}_t{t:03d}'
				ev_stored[ev][t] = LpVariable('ev_stored_' + increment, lowBound=0)
				p_ev_charge[ev][t] = LpVariable('p_ev_charge_' + increment, lowBound=0)
				p_ev_discharge[ev][t] = LpVariable('p_ev_discharge_' + increment, lowBound=0)
			# EWH decision variables
			if bool(self._ewh_dataset):
				for e in self.set_ewh:
					increment = f'{e}_t{t:07d}'
					# Temperature of water at EWH outlet at the beginning of time interval t (°C)
					temp[e][t] = LpVariable(f'temp_' + increment, lowBound=0)
					# Total energy balance of prosumer’s EWH at time interval t (kWh)
					w_tot[e][t] = LpVariable(f'w_tot_' + increment, lowBound=0)
					# Energy into the prosumer’s EWH at time interval t (kWh)
					w_in[e][t] = LpVariable(f'w_in_' + increment, lowBound=0)
					# Thermal energy losses at time interval t (kWh)
					w_loss[e][t] = LpVariable(f'w_loss_' + increment)
					# Binary variable for EWH operation status (1 = ON, 0 = OFF)
					delta_in[e][t] = LpVariable(f'delta_in_' + increment, lowBound=0, upBound=1)
					# Amount of energy stored in the EWH after usage and mixing with inlet
					w_water[e][t] = LpVariable(f'w_water_' + increment, lowBound=0)
					# Extra cost associated with water temperature reaching below comfort
					costComfort[e][t] = LpVariable(f'costComfort_' + increment, lowBound=0)
					# Binary Variable for if-else expression 15
					binAux[e][t] = LpVariable(f'binAux_' + increment, cat=LpBinary)
					# Pricing of that specific energy usage
					energyEWH[e][t] = LpVariable(f'energyEWH_' + increment, lowBound=0)

			if self._hvac is not None:
				for h in self.set_hvac:
					increment = f'{h}_t{t:03d}'
					self.hvac_temp[h][t] = LpVariable(f'hvac_temp_' + increment, lowBound=0)
					self.hvac_power[h][t] = LpVariable(f'hvac_power_' + increment, lowBound=0)
					self.delta_hvac[h][t] = LpVariable(f'delta_hvac_' + increment, lowBound=0, upBound=5, cat=LpInteger)
					self.hvac_active[h][t]= LpVariable(f'hvac_active_' + increment,lowBound=0, upBound=1, cat=LpBinary)
					self.hvac_aux[h][t] = LpVariable(f'hvac_aux_' + increment, lowBound=0, upBound=1,cat=LpBinary)
					self.hvac_mode[h][t] = LpVariable(f'hvac_mode_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					self.hvac_cost_comfort[h][t] = LpVariable(f'hvac_cost_comfort_' + increment, lowBound=0)
					self.hvac_mode_heat[h][t] = LpVariable(f'hvac_mode_heat_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					self.hvac_mode_off[h][t] = LpVariable(f'hvac_mode_off_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					self.hvac_mode_cool[h][t] = LpVariable(f'hvac_mode_cool_' + increment, lowBound=0, upBound=1, cat=LpBinary)

			if self._hp is not None:
				for hp in self.set_hp:
					increment = f'{hp}_t{t:03d}'

					self.hp_temp_indoor[hp][t] = LpVariable(f'hp_temp_indoor_' + increment, lowBound=0)
					self.hp_temp_outlet[hp][t] = LpVariable(f'hp_temp_outlet_' + increment, lowBound=0)
					self.hp_power[hp][t] = LpVariable(f'power_hp_' + increment, lowBound=0)
					self.hp_active[hp][t] = LpVariable(f'hp_active_' + increment, lowBound=0, upBound=1, cat=LpBinary)
					self.hp_cost_comfort[hp][t] = LpVariable(f'hp_cost_comfort_' + increment, lowBound=0)
					self.hp_active[hp][t] = LpVariable(f'hp_active_' + increment, cat=LpBinary)
					self.heating_kwh[hp][t] = LpVariable(f'hp_power_heating_' + increment, lowBound=0)
					self.circulation_kw[hp][t] = LpVariable(f'hp_power_circulation_' + increment, lowBound=0)
					self.tank_heating_kwh[hp][t] = LpVariable(f'hp_power_tank_' + increment, lowBound=0)
					self.hp_temp_return[hp][t] = LpVariable(f'hp_temp_return_' + increment, lowBound=0)
					self.hp_lost_power[hp][t] = LpVariable(f'hp_lost_power_' + increment, lowBound=0)

		# Eq. 1: Objective Function
		objective = lpSum(
			e_sup_retail[t] * self._l_buy[t]
			- e_sur_retail[t] * self._l_sell[t]
			+ e_sup_market[t] * self._l_market_buy[t]
			- e_sur_market[t] * self._l_market_sell[t]
			+ p_extra[t] * self._l_extra
			+ lpSum(self._deg_cost[b] * e_bd[b][t] for b in self.set_btm_storage)
			+ lpSum(costComfort[e][t] * 100 for e in self.set_ewh)
			for t in self.time_series
		)

		for t in self.time_series:
			if t != 0:
				objective += lpSum(self.hvac_cost_comfort[h][t] * 100 for h in self.set_hvac) + lpSum(self.hp_cost_comfort[hp][t] * 1 for hp in self.set_hp)




		self.milp += objective, 'Objective Function'

		# Eq. 2-8: Constraints
		for t in self.time_series:
			increment = f'{t:03d}'

			# Eq. 2
			self.milp += \
				e_cmet[t] == e_sup_retail[t] + e_sup_market[t] - e_sur_retail[t] - e_sur_market[t], \
				'Equilibrium_' + increment

			# Eq. 3
			# UPDATED WITH DISAGREGGATED EWH MODULES (ORIGINAL AND OPTIMIZED LOADS)
			self.milp += \
				e_cmet[t] == self._e_c[t] - self._e_g[t] \
				+ lpSum(e_bc[b][t] - e_bd[b][t] for b in self.set_btm_storage) + \
				+ lpSum(p_ev_charge[ev][t] - p_ev_discharge[ev][t]
				 for ev in self.set_btm_evs) + \
				lpSum(- varBackpack[e]['original_load'][t] + energyEWH[e][t] for e in self.set_ewh) + \
				lpSum(self.hvac_power[h][t] * self._delta_t for h in self.set_hvac) + \
				lpSum(self.hp_power[h][t] for h in self.set_hp), \
				'C_met_' + increment

			# Eq. 4
			self.milp += \
				- p_extra[t] - self._p_meter_max <= e_cmet[t] * 1 / self._delta_t, \
				'P_flow_low_limit_' + increment

			self.milp += \
				e_cmet[t] * 1 / self._delta_t <= p_extra[t] + self._p_meter_max, \
				'P_flow_high_limit_' + increment

			# Eq. 5
			self.milp += \
				e_sup_retail[t] + e_sup_market[t] <= self._big_m * delta_sup[t], \
				'Supply_ON_' + increment

			self.milp += \
				e_sur_retail[t] + e_sur_market[t] <= self._big_m * (1 - delta_sup[t]), \
				'Supply_OFF_' + increment

		for b, t in itertools.product(self.set_btm_storage, self.time_series):
			increment = f'{b}_t{t:03d}'

			# Eq. 6
			energy_update = e_bc[b][t] * self._eff_bc[b] - e_bd[b][t] * 1 / self._eff_bd[b]
			if t == 0:
				self.milp += \
					e_bat[b][t] == self._init_e_bat[b] + energy_update, \
					'SOC_update_' + increment
			else:
				self.milp += \
					e_bat[b][t] == e_bat[b][t - 1] + energy_update, \
					'SOC_update_' + increment

			# Eq. 7
			self.milp += \
				soc_bat[b][t] == e_bat[b][t] * 100 / self._e_bn[b], \
				'Energy_to_SOC_' + increment

			self.milp += \
				soc_bat[b][t] >= self._soc_min[b], \
				'Minimum_SOC_' + increment

			self.milp += \
				soc_bat[b][t] <= self._soc_max[b], \
				'Maximum_SOC_' + increment

			# Eq. 8
			self.milp += \
				e_bc[b][t] * 1 / self._delta_t <= self._p_max[b] * delta_bc[b][t], \
				'Charge_rate_limit_' + increment

			self.milp += \
				e_bd[b][t] * 1 / self._delta_t <= self._p_max[b] * (1 - delta_bc[b][t]), \
				'Discharge_rate_limit' + increment

		for ev, t in itertools.product(self.set_btm_evs, self.time_series):
			increment = f'{ev}_t{t:03d}'
			# Eq. 10
			if t == 0:
				self.milp += ev_stored[ev][t] == self._init_e_ev[ev] + self._eff_bc_ev[ev] * p_ev_charge[ev][t] \
							 - (1/self._eff_bd_ev[ev]) * p_ev_discharge[ev][t] \
							 - self._trip_ev[ev][t],\
							 'EV_balance_' + increment
			else:
				self.milp += ev_stored[ev][t] == ev_stored[ev][t-1] + self._eff_bc_ev[ev] * p_ev_charge[ev][t] \
							  - (1 / self._eff_bd_ev[ev]) * p_ev_discharge[ev][t] - self._trip_ev[ev][t],\
							 'EV_balance_' + increment

			# Eq. 11
			self.milp += (1 / self._eff_bd_ev[ev]) * p_ev_discharge[ev][t] <= self._pmax_d_ev[ev] * \
						 self._bin_ev[ev][t] * self._delta_t, 'EV_Discharging_limit_' + increment

			# Eq. 12
			self.milp += self._eff_bc_ev[ev] * p_ev_charge[ev][t] <= self._pmax_c_ev[ev] * \
						 self._bin_ev[ev][t] * self._delta_t, 'EV_Charging_limit_' + increment

			# Eq. 13
			self.milp += ev_stored[ev][t] <= self._battery_capacity_ev[ev], 'EV_Max_capacity_' + increment

			# Eq. 14
			self.milp += ev_stored[ev][t] >= self._min_energy_storage_ev[ev], 'EV_Min_capacity_' + increment

		# EWH constraints
		if bool(self._ewh_dataset):
			for e, t in itertools.product(self.set_ewh, self.time_series):
				# Eq. (1)
				if t == 0:
					self.milp += w_tot[e][t] == self.wh_init[e], \
						f'Constraint_1_{e}_{t:07d}'
				else:
					self.milp += w_tot[e][t] == w_water[e][t - 1] + w_in[e][t - 1] - w_loss[e][t - 1], \
						f'Constraint_1_{e}_{t:07d}'
				# Eq. (2)
				self.milp += \
					w_in[e][t] == \
					self.ewh_power[e] * self.delta_t[e] * delta_in[e][t] * self.delta_t[e] * 60, \
						f'Constraint_2_{e}_{t:07d}'
				# Eq. (3) Pricing/Energy
				self.milp += energyEWH[e][t] == delta_in[e][t] * self.ewh_power[e] * self.delta_t[e], \
					f'Constraint_3_{e}_{t:07d}'
				# Eq. (4)
				if t == 0:
					self.milp += temp[e][t] == self.ewh_start_temp[e], f'Constraint_4_{e}_{t:07d}'
				else:
					self.milp += \
						temp[e][t] == \
						w_tot[e][t] * 3600 / \
						(self.delta_t[e] * 60) / \
						(self.ewh_capacity[e] * self.waterHeatCap[e]), \
							f'Constraint_4_{e}_{t:07d}'
				# Eq. (5)
				self.milp += \
					w_loss[e][t] == \
					self.heatTransferCoeff[e] * \
					self.ewh_area[e] * \
					(temp[e][t] - self.ambTemp[e]) * \
					self.delta_t[e] * \
					self.delta_t[e] * 60, \
						f'Constraint_5_{e}_{t:07d}'
				# Eq. (6)
				self.milp += self.wh_min[e] <= w_tot[e][t], f'Constraint_6.1_{e}_{t:07d}'
				self.milp += w_tot[e][t] <= self.wh_max[e], f'Constraint_6.2_{e}_{t:07d}'
				self.milp += self.ewh_min_temp[e] <= temp[e][t], f'Constraint_6.3_{e}_{t:07d}'
				self.milp += temp[e][t] <= self.ewh_max_temp[e], f'Constraint_6.4_{e}_{t:07d}'

				# Eq.(7) assure that in the (t) period after the end of hot water usage (t-1),
				# the EWH has, at least, 80L @ 45ºC [e][t]
				if (self.delta_use[e][t] - self.delta_use[e][t - 1] != 0) & \
						(self.delta_use[e][t] - self.delta_use[e][t - 1] == -self.delta_use[e][t-1]):
					# if delta_use[e][t] - delta_use[t-1] < 0:
					self.milp += \
						w_tot[e][t] >= \
						self.tempSet[e] * 1.005 * \
						self.ewh_capacity[e] * \
						self.waterHeatCap[e] / 3600 * \
						self.delta_t[e] * 60 - \
						costComfort[e][t], \
							f'Constraint_7.1_{e}_{t:07d}'
					self.milp += \
						w_tot[e][t-1] >= \
						self.tempSet[e] * 1.005 * \
						self.ewh_capacity[e] * \
						self.waterHeatCap[e] / 3600 * \
						self.delta_t[e] * 60 - \
						costComfort[e][t-1], \
							f'Constraint_7.2_{e}_{t:07d}'

				# Eq.(8) Internal water energy after usage
				if self.delta_use[e][t] > 0:
					# binary definition with temp[e][t]
					self.milp += temp[e][t] >= \
								 self.tempSet[e] - self.bigNumber[e] * (1 - binAux[e][t]), \
						f'Constraint_8.1_{e}_{t:07d}'
					self.milp += temp[e][t] <= \
								 self.tempSet[e] + self.bigNumber[e] * binAux[e][t], \
						f'Constraint_8.2_{e}_{t:07d}'
					# if temp[e][t] > tempSet
					self.milp += w_water[e][t] >= \
								 self.regressor_aboveSet_m_temp[e] * temp[e][t] + \
								 self.regressor_aboveSet_m_delta[e] * self.delta_use[e][t] + \
								 self.regressor_aboveSet_b[e] - \
								 self.bigNumber[e] * (1 - binAux[e][t]), \
						f'Constraint_8.3_{e}_{t:07d}'
					self.milp += w_water[e][t] <= \
								 self.regressor_aboveSet_m_temp[e] * temp[e][t] + \
								 self.regressor_aboveSet_m_delta[e] * self.delta_use[e][t] + \
								 self.regressor_aboveSet_b[e] + \
								 self.bigNumber[e] * (1 - binAux[e][t]), \
						f'Constraint_8.4_{e}_{t:07d}'
					# else
					self.milp += w_water[e][t] >= \
								 self.regressor_belowSet_m_temp[e] * temp[e][t] + \
								 self.regressor_belowSet_m_delta[e] * self.delta_use[e][t] + \
								 self.regressor_belowSet_b[e] - \
								 self.bigNumber[e] * binAux[e][t], \
						f'Constraint_8.5_{e}_{t:07d}'
					self.milp += w_water[e][t] <= \
								 self.regressor_belowSet_m_temp[e] * temp[e][t] + \
								 self.regressor_belowSet_m_delta[e] * self.delta_use[e][t] + \
								 self.regressor_belowSet_b[e] + \
								 self.bigNumber[e] * binAux[e][t], \
						f'Constraint_8.6_{e}_{t:07d}'
				else:
					self.milp += w_water[e][t] == \
								 temp[e][t] * self.ewh_capacity[e] * self.waterHeatCap[e] / 3600 * \
								 self.delta_t[e] * 60, \
						f'Constraint_8.7_{e}_{t:07d}'

		# HVAC Constraints
		if self._hvac is not None:
			for h, t in itertools.product(self.set_hvac, self.time_series):
				increment = f'{h}_{t:03d}'

				# Temperature Evolution Equation
				if t == 0:
					self.milp += self.hvac_temp[h][t] == self.hvac_init_temp[h], f'HVAC_Start_Temp_' + increment

				if self.type[h] == 'inverter':
					if t !=0:
						#Heating equation
						self.milp += (
								self.hvac_temp[h][t]
								- self.hvac_temp[h][t - 1]
								- self.mu[h] * (self.T_out[h][t] - self.hvac_temp[h][t - 1])
								- self.psi[h] * self.hvac_power[h][t] * self._delta_t
								<= self._big_m * (1 - self.hvac_mode[h][t])
						), f'HVAC_Heating_UB_' + increment
						self.milp += (
								self.hvac_temp[h][t]
								- self.hvac_temp[h][t - 1]
								- self.mu[h] * (self.T_out[h][t] - self.hvac_temp[h][t - 1])
								- self.psi[h] * self.hvac_power[h][t] * self._delta_t
								>= -self._big_m * (1 - self.hvac_mode[h][t])
						), f'HVAC_Heating_LB_' + increment

						# Cooling equation
						self.milp += (
								self.hvac_temp[h][t]
								- self.hvac_temp[h][t - 1]
								- self.mu[h] * (self.T_out[h][t] - self.hvac_temp[h][t - 1])
								+ self.psi[h] * self.hvac_power[h][t] * self._delta_t
								<= self._big_m * self.hvac_mode[h][t]
						), f'HVAC_Cooling_UB_' + increment
						self.milp += (
								self.hvac_temp[h][t]
								- self.hvac_temp[h][t - 1]
								- self.mu[h] * (self.T_out[h][t] - self.hvac_temp[h][t - 1])
								+ self.psi[h] * self.hvac_power[h][t] * self._delta_t
								>= -self._big_m * self.hvac_mode[h][t]
						), f'HVAC_Cooling_LB_' + increment
					self.milp += self.delta_hvac[h][t] <= 5, f'HVAC_Activation_Control_' + increment
					self.milp += self.hvac_power[h][t] == 0.2 * self.delta_hvac[h][t] * self.hvac_capacity[h], f'HVAC_Power_Level_' + increment

				if self.type[h] == 'state':
					if t !=0:
						if t != 0:
							self.milp += (self.hvac_mode_heat[h][t] + self.hvac_mode_off[h][t] + self.hvac_mode_cool[h][
								t] == 1), f'HVAC_mode_sum_' + increment
							# Heating mode
							self.milp += (self.hvac_temp[h][t] <= (
									self.T_out[h][t] + self.hvac_power[h][t] * self.thermal_resist[h] - (
									self.T_out[h][t] + self.hvac_power[h][t] * self.thermal_resist[h] -
									self.hvac_temp[h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[h] * self.thermal_cap[h])))
										  + self._big_m * (1 - self.hvac_mode_heat[h][
										t])), f'HVAC_Heating_UB_state' + increment
							self.milp += (self.hvac_temp[h][t] >= (
									self.T_out[h][t] + self.hvac_power[h][t] * self.thermal_resist[h] - (
									self.T_out[h][t] + self.hvac_power[h][t] * self.thermal_resist[h] -
									self.hvac_temp[h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[h] * self.thermal_cap[h])))
										  - self._big_m * (1 - self.hvac_mode_heat[h][
										t])), f'HVAC_Heating_LB_state' + increment

							# off mode
							self.milp += (self.hvac_temp[h][t] <= (
									self.T_out[h][t] - (
									self.T_out[h][t] -
									self.hvac_temp[h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[h] * self.thermal_cap[h])))
										  + self._big_m * (
													  1 - self.hvac_mode_off[h][t])), f'HVAC_Off_UB_state' + increment
							self.milp += (self.hvac_temp[h][t] >= (
									self.T_out[h][t] - (
									self.T_out[h][t] -
									self.hvac_temp[h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[h] * self.thermal_cap[h])))
										  - self._big_m * (
													  1 - self.hvac_mode_off[h][t])), f'HVAC_Off_LB_state' + increment

							# Cooling mode
							self.milp += (self.hvac_temp[h][t] <= (
									self.T_out[h][t] - self.hvac_power[h][t] * self.thermal_resist[h] - (
									self.T_out[h][t] - self.hvac_power[h][t] * self.thermal_resist[h] -
									self.hvac_temp[h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[h] * self.thermal_cap[h])))
										  + self._big_m * (1 - self.hvac_mode_cool[h][
										t])), f'HVAC_Cooling_UB_state' + increment
							self.milp += (self.hvac_temp[h][t] >= (
									self.T_out[h][t] - self.hvac_power[h][t] * self.thermal_resist[h] - (
									self.T_out[h][t] - self.hvac_power[h][t] * self.thermal_resist[h] -
									self.hvac_temp[h][t - 1]) * math.exp(
								- self._delta_t / (self.thermal_resist[h] * self.thermal_cap[h])))
										  - self._big_m * (1 - self.hvac_mode_cool[h][
										t])), f'HVAC_Cooling_LB_state' + increment

						self.milp += self.hvac_active[h][t] == self.hvac_mode_heat[h][t] + self.hvac_mode_cool[h][
							t], f'HVAC_Active_Link_' + increment
						self.milp += self.hvac_power[h][t] == self.hvac_active[h][t] * self.hvac_capacity[
							h], f'HVAC_On_Off_' + increment

				self.milp += self.hvac_temp[h][t] - self.hvac_temp_max[h] <= self.hvac_cost_comfort[h][t]
				self.milp += self.hvac_temp[h][t] - self.hvac_temp_min[h] >= -self.hvac_cost_comfort[h][t]

		if self._hp is not None:
			for hp, t in itertools.product(self.set_hp, self.time_series):
				if self.hp_type[hp] =='thermostat':

					increment = f'{hp}_{t:03d}'


					# HPT-1: HP energy consumed = rated_power * active[t] * delta_t
					self.milp += (self.hp_power[hp][t] == self.hp_power_rated[hp] * self.hp_active[hp][t] * self._delta_t), f'HP_Energy_' + increment

					# HPT-2.1
					self.milp += (self.hp_power_rated[hp] * self.hp_active[hp][t] == self.heating_kwh[hp][t] + self.circulation_kw[hp][t] + self.tank_heating_kwh[hp][t] + self.hp_lost_power[hp][t]), f'HP_Total_Power_' + increment

					# HPT-2.2
					self.milp += (self.heating_kwh[hp][t] >= self.hp_mass_hw_demand[hp][t] * self.hp_c_p[hp] * (self.hp_temp_desired[hp] - self.hp_temp_inlet[hp]) * self._delta_t/3600), f'HP_Heating_Demand_' + increment

					# HPT-2.3
					self.milp += (self.circulation_kw[hp][t] >= self.hp_mass_radiator[hp][t] * self.hp_c_p[hp] * (self.hp_temp_outlet[hp][t] - self.hp_temp_return[hp][t]) * self._delta_t/3600), f'HP_Circulation_Power_' + increment

					# HPT-2.5
					# if t ==0:
					# 	self.milp += (self.tank_heating_kwh[hp][t] == self.hp_capacity_tank[hp] * self.hp_c_p[hp] * self.hp_temp_out_init[hp]), f'HP_Tank_Init_' + increment
					if t != 0:
						# HPT-2.4
						self.milp += (self.tank_heating_kwh[hp][t] >= self.hp_capacity_tank[hp] * self.hp_c_p[hp] * (
									self.hp_temp_outlet[hp][t] - self.hp_temp_outlet[hp][t-1]) * self._delta_t/3600), f'HPT2.4_Tank_Heating_' + increment

					# HPT-3
					# self.milp += self.circulation_kw[hp][t] == ((self.hp_h_rad[hp] * self.hp_area_rad[hp]) * ((self.hp_temp_outlet[hp][t]
					# 										+ self.hp_temp_return[hp][t])/2 - self.hp_temp_indoor[hp][t])), f'HP_Convective_Limit_' + increment

					self.milp += (self.hp_mass_radiator[hp][t] * self.hp_c_p[hp] * (
								self.hp_temp_outlet[hp][t] - self.hp_temp_return[hp][t]) * self._delta_t / 3600) == ((self.hp_h_rad[hp] * self.hp_area_rad[hp]) * ((self.hp_temp_outlet[hp][t]
															+ self.hp_temp_return[hp][t])/2 - self.hp_temp_indoor[hp][t])* self._delta_t / 3600), f'HP_Convective_Limit_' + increment

					# if t != 0:
					# 	# Radiator‐loop mixing: the tank at t is the remaining hot water plus the colder radiator return
					# 	self.milp += (self.hp_temp_outlet[hp][t] * self.hp_capacity_tank[hp]
					# 						== self.hp_temp_outlet[hp][t - 1] * (self.hp_capacity_tank[hp] - self.hp_mass_radiator[hp][t])
					# 						+ self.hp_temp_return[hp][t] * self.hp_mass_radiator[hp][t] ), f'HP_Radiator_Mixing_{hp}_{t}'


					# HPT-4.1/ 4.2: Indoor temperature evolution
					if t == 0:
						self.milp += (self.hp_temp_indoor[hp][t] == self.hp_temp_indoor_init[hp]), f'HP_Indoor_Init_' + increment
						self.milp += (self.hp_temp_outlet[hp][t] == self.hp_temp_out_init[hp]), f'HP_Outlet_Init_' + increment
					else:
						# self.milp += ( self.hp_temp_indoor[h][t] == self.hp_temp_indoor[h][t - 1]
						# 					+ (self._delta_t / self.hp_thermal_resistance[h]) * self.hp_u_value[h] * (self.hp_t_out[h][t - 1] - self.hp_temp_indoor[h][t - 1])
						# 					+ self.hp_h_rad[h] * self.hp_area_rad[h] * (self.hp_temp_outlet[h][t - 1] - self.hp_temp_indoor[h][t - 1])
						# 			 ), f'HP_Indoor_Evolution_' + increment

						self.milp += (self.hp_temp_indoor[hp][t] == self.hp_temp_indoor[hp][t - 1] * self.hp_u_value[hp] + self.hp_t_out[hp][t - 1] * (self._delta_t / self.hp_thermal_resistance[hp])
									  + self.hp_h_rad[hp] * self.hp_area_rad[hp] * self.hp_temp_outlet[hp][t]), f'HP_Indoor_Evolution_' + increment


					# HPT-5
					self.milp += (self.hp_temp_indoor[hp][t] + self.hp_cost_comfort[hp][t] >= self.hp_temp_indoor_min[hp]), f'HP_Temp_Min_WithSlack_' + increment
					self.milp += (self.hp_temp_indoor[hp][t] + self.hp_cost_comfort[hp][t] <= self.hp_temp_indoor_max[hp]), f'HP_Temp_Max_WithSlack_' + increment
					# HPT-5
					self.milp += (self.hp_temp_outlet[hp][t] + self.hp_cost_comfort[hp][t] >= self.hp_temp_out_min[hp]), f'HP_TempOut_Min_WithSlack_' + increment
					self.milp += (self.hp_temp_outlet[hp][t] + self.hp_cost_comfort[hp][t] <= self.hp_temp_out_max[hp]), f'HP_TempOut_Max_WithSlack_' + increment

				if self.hp_type[hp] == 'inverter':

					increment = f'{hp}_{t:03d}'

					self.milp += self.hp_power[hp][t] <= self.hp_power_rated[hp]

					# HPT-2.1
					self.milp += (self.hp_power[hp][t] >= self.heating_kwh[hp][t] +
								self.circulation_kw[hp][t] + self.tank_heating_kwh[hp][t]), f'HP_Total_Power_' + increment

					# HPT-2.2
					self.milp += (self.heating_kwh[hp][t] >= self.hp_mass_hw_demand[hp][t] * self.hp_c_p[hp] * (
								self.hp_temp_desired[hp] - self.hp_temp_inlet[
							hp])/ 3600 * self._delta_t), f'HP_Heating_Demand_' + increment

					# HPT-2.3
					self.milp += (self.circulation_kw[hp][t] >= self.hp_mass_radiator[hp][t] * self.hp_c_p[hp] * (
								self.hp_temp_outlet[hp][t] - self.hp_temp_return[hp][
							t])/ 3600 * self._delta_t), f'HP_Circulation_Power_' + increment

					# HPT-2.5
					# if t ==0:
					# 	self.milp += (self.tank_heating_kwh[hp][t] == self.hp_capacity_tank[hp] * self.hp_c_p[hp] * self.hp_temp_out_init[hp]/3600), f'HP_Tank_Init_' + increment
					if t != 0:
						# HPT-2.4
						self.milp += (self.tank_heating_kwh[hp][t] >= self.hp_capacity_tank[hp] * self.hp_c_p[hp] * (
								self.hp_temp_outlet[hp][t] - self.hp_temp_outlet[hp][
							t - 1])/ 3600 * self._delta_t), f'HPT2.4_Tank_Heating_' + increment

					# HPT-3
					# self.milp += self.circulation_kw[hp][t] == ((self.hp_h_rad[hp] * self.hp_area_rad[hp]) * ((self.hp_temp_outlet[hp][t]
					# 										+ self.hp_temp_return[hp][t])/2 - self.hp_temp_indoor[hp][t])), f'HP_Convective_Limit_' + increment

					self.milp += (self.hp_mass_radiator[hp][t] * self.hp_c_p[hp] * (
							self.hp_temp_outlet[hp][t] - self.hp_temp_return[hp][t]) / 3600) == (
											(self.hp_h_rad[hp] * self.hp_area_rad[hp]) * ((self.hp_temp_outlet[hp][t]
											+ self.hp_temp_return[hp][t]) / 2 - self.hp_temp_indoor[hp][t]) * self._delta_t), f'HP_Convective_Limit_' + increment


					# HPT-4.1/ 4.2: Indoor temperature evolution
					if t == 0:
						self.milp += (self.hp_temp_indoor[hp][t] == self.hp_temp_indoor_init[hp]), f'HP_Indoor_Init_' + increment
						self.milp += (self.hp_temp_outlet[hp][t] == self.hp_temp_out_init[hp]), f'HP_Outlet_Init_' + increment
					else:
						# self.milp += ( self.hp_temp_indoor[h][t] == self.hp_temp_indoor[h][t - 1]
						# 					+ (self._delta_t / self.hp_thermal_resistance[h]) * self.hp_u_value[h] * (self.hp_t_out[h][t - 1] - self.hp_temp_indoor[h][t - 1])
						# 					+ self.hp_h_rad[h] * self.hp_area_rad[h] * (self.hp_temp_outlet[h][t - 1] - self.hp_temp_indoor[h][t - 1])
						# 			 ), f'HP_Indoor_Evolution_' + increment

						self.milp += (self.hp_temp_indoor[hp][t] == self.hp_temp_indoor[hp][t - 1] * self.hp_u_value[hp] +
									  self.hp_t_out[hp][t - 1] * (self._delta_t / self.hp_thermal_resistance[hp])
									  + self.hp_h_rad[hp] * self.hp_area_rad[hp] * self.hp_temp_outlet[hp][
										  t]), f'HP_Indoor_Evolution_' + increment

					# HPT-5
					self.milp += (self.hp_temp_indoor[hp][t] + self.hp_cost_comfort[hp][t] >= self.hp_temp_indoor_min[
						hp]), f'HP_Temp_Min_WithSlack_' + increment
					self.milp += (self.hp_temp_indoor[hp][t] + self.hp_cost_comfort[hp][t] <= self.hp_temp_indoor_max[
						hp]), f'HP_Temp_Max_WithSlack_' + increment
					# HPT-5
					# self.milp += (self.hp_temp_outlet[hp][t] + self.hp_cost_comfort[hp][t] >= self.hp_temp_out_min[
					# 	hp]), f'HP_TempOut_Min_WithSlack_' + increment
					# self.milp += (self.hp_temp_outlet[hp][t] + self.hp_cost_comfort[hp][t] <= self.hp_temp_out_max[
					# 	hp]), f'HP_TempOut_Max_WithSlack_' + increment

		# Write MILP to .lp file
		dir_name = os.path.abspath(os.path.join(__file__, '..'))
		lp_file = os.path.join(dir_name, f'Stage1_{n}.lp')
		self.milp.writeLP(lp_file)

		# Set the solver to be called
		if self.solver == 'CBC' and 'PULP_CBC_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(pulp.PULP_CBC_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap))

		elif self.solver == 'GUROBI' and 'GUROBI_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(GUROBI_CMD(msg=False, timeLimit=self.timeout, options=[("MIPGap", self.mipgap)]))

		elif self.solver == 'CPLEX' and 'CPLEX_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(CPLEX_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap))

		elif self.solver == 'HiGHS' and 'HiGHS_CMD' in listSolvers(onlyAvailable=True):
			self.milp.setSolver(HiGHS_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap, threads=1))

		else:
			raise ValueError(f'{self.solver}_CMD not available in puLP; '
							 f'please install the required solver or try a different one')

		return

	def solve_milp(self):
		"""
		Function that heads the definition and solution of the first stage MILP.
		"""
		# Define the MILP
		self.__define_milp()

		# Solve the MILP
		logger.debug(f'-- solving the individual MILP problem for Meter id: {self.meter_id}...')

		try:
			self.milp.solve()
			self.status = LpStatus[self.milp.status]
			self.obj_value = value(self.milp.objective)

		except Exception as ex:
			logger.error(f'Solver raised an error: \'{ex}\'. Considering problem as "Infeasible".')
			exit()

		# Case when no objective value is found since all data is 0 (for testing purposes)
		if self.status == 'Optimal' and self.obj_value is None:
			self.obj_value = 0

		logger.debug(f'-- solving the individual MILP problem for Meter id: {self.meter_id}... DONE!')

		return

	def generate_outputs(self) -> OutputsS1Dict:
		"""
		Function for generating the outputs of optimization, namely the battery's set points.
		:return: outputs dictionary with MILP variables' and other computed values
		"""
		logger.debug(f'-- generating outputs from the individual MILP problem for Meter id: {self.meter_id}...')

		outputs = {}

		# -- Verification added to avoid raising error whenever encountering a puLP solver error with CBC
		if self.obj_value is None:
			return outputs

		outputs['meter_id'] = self.meter_id
		outputs['obj_value'] = self.obj_value
		outputs['milp_status'] = self.status

		outputs['e_sup_retail'] = none_lists(self.time_intervals)
		outputs['e_sur_retail'] = none_lists(self.time_intervals)
		outputs['e_sup_market'] = none_lists(self.time_intervals)
		outputs['e_sur_market'] = none_lists(self.time_intervals)
		outputs['delta_sup'] = none_lists(self.time_intervals)
		outputs['e_cmet'] = none_lists(self.time_intervals)
		outputs['p_extra'] = none_lists(self.time_intervals)
		outputs['e_bat'] = dict_none_lists(self.time_intervals, self.set_btm_storage)
		outputs['soc_bat'] = dict_none_lists(self.time_intervals, self.set_btm_storage)
		outputs['e_bc'] = dict_none_lists(self.time_intervals, self.set_btm_storage)
		outputs['e_bd'] = dict_none_lists(self.time_intervals, self.set_btm_storage)
		outputs['delta_bc'] = dict_none_lists(self.time_intervals, self.set_btm_storage)
		if self.set_btm_evs != []:
			outputs['ev_stored'] = dict_none_lists(self.time_intervals, self.set_btm_evs)
			outputs['p_ev_charge'] = dict_none_lists(self.time_intervals, self.set_btm_evs)
			outputs['p_ev_discharge'] = dict_none_lists(self.time_intervals, self.set_btm_evs)


		# required when vars include "-" since puLP converts it to "_"
		btm_storage_ids = [bid for bid in self.set_btm_storage]
		b_match = {key: key.replace('-', '_') for key in btm_storage_ids}

		btm_evs_ids = [bid for bid in self.set_btm_evs]
		ev_match = {key: key.replace('-', '_') for key in btm_evs_ids}

		for v in self.milp.variables():
			step_nr = None
			if not re.search('dummy', v.name):
				step_nr = int(v.name[-3:])
			if re.search('e_sup_retail', v.name):
				outputs['e_sup_retail'][step_nr] = v.varValue
			elif re.search('e_sur_retail', v.name):
				outputs['e_sur_retail'][step_nr] = v.varValue
			elif re.search('e_sup_market', v.name):
				outputs['e_sup_market'][step_nr] = v.varValue
			elif re.search('e_sur_market', v.name):
				outputs['e_sur_market'][step_nr] = v.varValue
			elif re.search('delta_sup', v.name):
				outputs['delta_sup'][step_nr] = v.varValue
			elif re.search('e_cmet', v.name):
				outputs['e_cmet'][step_nr] = v.varValue
			elif re.search('p_extra', v.name):
				outputs['p_extra'][step_nr] = v.varValue
			else:
				for b_ in self.set_btm_storage:
					b = b_match[b_]
					if re.search(f'e_bat_{b}_', v.name):
						outputs['e_bat'][b_][step_nr] = v.varValue
						break
					elif re.search(f'soc_bat_{b}_', v.name):
						outputs['soc_bat'][b_][step_nr] = v.varValue
						break
					elif re.search(f'e_bc_{b}_', v.name):
						outputs['e_bc'][b_][step_nr] = v.varValue
						break
					elif re.search(f'e_bd_{b}_', v.name):
						outputs['e_bd'][b_][step_nr] = v.varValue
						break
					elif re.search(f'delta_bc_{b}_', v.name):
						outputs['delta_bc'][b_][step_nr] = v.varValue
						break
			# EVs output
			if self.set_btm_evs != []:
				for ev_ in self.set_btm_evs:
					ev = ev_match[ev_]
					if re.search(f'ev_stored_{ev}_', v.name):
						outputs['ev_stored'][ev_][step_nr] = v.varValue
					if re.search(f'p_ev_charge_{ev}_', v.name):
						outputs['p_ev_charge'][ev_][step_nr] = v.varValue
					if re.search(f'p_ev_discharge_{ev}_', v.name):
						outputs['p_ev_discharge'][ev_][step_nr] = v.varValue

		# EWH outputs
		if bool(self._ewh_dataset):

			outputs['ewh_temp'] = dict_none_lists(self.time_intervals, self.set_ewh)
			outputs['ewh_delta_in'] = dict_none_lists(self.time_intervals, self.set_ewh)
			outputs['ewh_optimized_load'] = dict_none_lists(self.time_intervals, self.set_ewh)
			outputs['ewh_original_load'] = dict_none_lists(self.time_intervals, self.set_ewh)
			outputs['ewh_delta_use'] = dict_none_lists(self.time_intervals, self.set_ewh)

			for v in self.milp.variables():
				step_nr = None
				if not re.search('dummy', v.name):
					step_nr = int(v.name[-3:])
				for e in self.set_ewh:
					## find variables and store data
					if re.search(f'temp_{e}_', v.name):
						outputs['ewh_temp'][e][step_nr] = v.varValue
					if re.search(f'delta_in_{e}_', v.name):
						outputs['ewh_delta_in'][e][step_nr] = v.varValue
						outputs['ewh_optimized_load'][e][step_nr] = v.varValue * varBackpack[e]['ewh_power']
					outputs['ewh_original_load'][e] = varBackpack[e]['original_load']
					outputs['ewh_delta_use'][e] = varBackpack[e]['delta_use']


		# HVAC Outputs
		if self._hvac is not None:

			outputs['hvac_temp'] = dict_none_lists(self.time_intervals, self.set_hvac)
			outputs['hvac_power'] = dict_none_lists(self.time_intervals, self.set_hvac)
			outputs['cost_comfort'] = dict_none_lists(self.time_intervals, self.set_hvac)

			for v in self.milp.variables():
				step_nr = None
				if not re.search('dummy', v.name):
					step_nr = int(v.name[-3:])

				for h in self.set_hvac:
					# Find variables and store data
					if re.search(f'hvac_temp_{h}_', v.name):
						outputs['hvac_temp'][h][step_nr] = v.varValue
					if re.search(f'hvac_power_{h}_', v.name):
						outputs['hvac_power'][h][step_nr] = v.varValue
					if re.search(f'hvac_cost_comfort_{h}_', v.name):
						outputs['cost_comfort'][h][step_nr] = v.varValue

		if self._hp is not None:

			outputs['hp_indoor_temp'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_outlet_temp'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_power'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_cost_comfort'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_power_heating'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_power_circulation'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_power_tank'] = dict_none_lists(self.time_intervals, self.set_hp)
			outputs['hp_temp_return'] = dict_none_lists(self.time_intervals, self.set_hp)

			for v in self.milp.variables():
				step_nr = None
				if not re.search('dummy', v.name):
					step_nr = int(v.name[-3:])

				for h in self.set_hp:
					# Find variables and store data
					if re.search(f'hp_temp_indoor_{h}_', v.name):
						outputs['hp_indoor_temp'][h][step_nr] = v.varValue
					if re.search(f'hp_temp_outlet_{h}_', v.name):
						outputs['hp_outlet_temp'][h][step_nr] = v.varValue
					if re.search(f'power_hp_{h}_', v.name):
						outputs['hp_power'][h][step_nr] = v.varValue
					if re.search(f'hp_cost_comfort_{h}_', v.name):
						outputs['hp_cost_comfort'][h][step_nr] = v.varValue
					if re.search(f'hp_power_heating_{h}_', v.name):
						outputs['hp_power_heating'][h][step_nr] = v.varValue
					if re.search(f'hp_power_circulation_{h}_', v.name):
						outputs['hp_power_circulation'][h][step_nr] = v.varValue
					if re.search(f'hp_power_tank_{h}_', v.name):
						outputs['hp_power_tank'][h][step_nr] = v.varValue
					if re.search(f'hp_temp_return_{h}_', v.name):
						outputs['hp_temp_return'][h][step_nr] = v.varValue

		# Calculate the cost of degradation
		deg_cost = 0
		for b, t in itertools.product(self.set_btm_storage, self.time_series):
			deg_cost += self._deg_cost[b] * outputs['e_bd'][b][t]
		outputs['deg_cost'] = deg_cost

		# Calculate the cost that came from overstepping the maximum Meter power limit
		p_extra = sum(outputs['p_extra'])
		p_extra_cost = p_extra * self._l_extra
		outputs['p_extra_cost'] = p_extra_cost

		# Retrieve the cost with energy of each Meter obtained in Stage 1
		outputs['c_ind'] = self.obj_value

		# Calculate additional terms that do not consider the cost of degradation and/or extra power at Meter
		outputs['c_ind_without_deg'] = outputs['c_ind'] - deg_cost
		outputs['c_ind_without_p_extra'] = outputs['c_ind'] - p_extra_cost
		outputs['c_ind_without_deg_and_p_extra'] = outputs['c_ind'] - deg_cost - p_extra_cost

		logger.debug(f'-- generating outputs from the individual MILP problem for Meter id: {self.meter_id}... DONE!')

		return outputs
