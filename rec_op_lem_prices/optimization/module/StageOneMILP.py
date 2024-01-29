"""
Class for implementing and running the Stage 1 MILP for each individual Meter / microgrid / hybrid park.
"""
import itertools
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
	LpBinary,
	LpMinimize,
	LpProblem,
	LpStatus,
	lpSum,
	LpVariable,
	GUROBI_CMD,
	pulp,
	value
)


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
		self._eff_bc = {}  # charging efficiency of the batteries [%]
		self._eff_bd = {}  # discharging efficiency of the batteries [%]
		self._p_max = {}  # maximum input and output batteries' power [kW]
		self._e_bn = {}  # nominal capacity of the batteries of n [kWh]
		self._soc_min = {}  # minimum state of charge [%]
		self._soc_max = {}  # maximum state of charge [%]
		self._init_e_bat = {}  # initial energy content of the batteries [kWh]
		self._deg_cost = {}  # estimated degradation cost of the batteries of n [€/kWh]
		self._big_m = 2 * self._p_meter_max  # a very big number [kWh]
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
		self.set_btm_storage = []  # stores the Meter's Btm storage assets' ids

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

		# Eq. 1: Objective Function
		objective = lpSum(
			e_sup_retail[t] * self._l_buy[t]
			- e_sur_retail[t] * self._l_sell[t]
			+ e_sup_market[t] * self._l_market_buy[t]
			- e_sur_market[t] * self._l_market_sell[t]
			+ p_extra[t] * self._l_extra
			+ lpSum(self._deg_cost[b] * e_bd[b][t] for b in self.set_btm_storage)
			for t in self.time_series
		)

		self.milp += objective, 'Objective Function'

		# Eq. 2-8: Constraints
		for t in self.time_series:
			increment = f'{t:03d}'

			# Eq. 2
			self.milp += \
				e_cmet[t] == e_sup_retail[t] + e_sup_market[t] - e_sur_retail[t] - e_sur_market[t], \
				'Equilibrium_' + increment

			# Eq. 3
			self.milp += \
				e_cmet[t] == self._e_c[t] - self._e_g[t] \
				+ lpSum(e_bc[b][t] - e_bd[b][t] for b in self.set_btm_storage), \
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

		# Write MILP to .lp file
		dir_name = os.path.abspath(os.path.join(__file__, '..'))
		lp_file = os.path.join(dir_name, f'Stage1_{n}.lp')
		self.milp.writeLP(lp_file)

		# Set the solver to be called
		if self.solver == 'CBC':
			self.milp.setSolver(pulp.PULP_CBC_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap))
		elif self.solver == 'GUROBI':
			# self.milp.setSolver(GUROBI_CMD(msg=True, timeLimit=self.timeout, mip=self.mipgap))
			self.milp.setSolver(GUROBI_CMD(msg=False))
		else:
			raise ValueError

		logger.debug(f'-- defining the individual MILP problem for Meter id: {self.meter_id}... DONE!')

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

		# required when vars include "-" since puLP converts it to "_"
		btm_storage_ids = [bid for bid in self.set_btm_storage]
		b_match = {key: key.replace('-', '_') for key in btm_storage_ids}

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
