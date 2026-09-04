from .ewh_power_functions import (create_usage_dataset, real_ewh_load_estimator, convert_load_usage)
from .ewh_opt_functions import (resample_data, build_varBackpack, update_dataset_backpack, linear_regressors, ewh_solver)

##############################################
##      Optimization Pipeline Function      ##
##############################################

def ewh_optimization(params_input, dataset, resample = 'no', optSolver = 'HiGHS', solverPath=None):
    varBackpack = build_varBackpack(params_input, dataset)
    if varBackpack['load_diagram_exists'] == 0:
        dataset = create_usage_dataset(dataset)
        dataset['load'] = real_ewh_load_estimator(dataset, varBackpack)
    if varBackpack['load_diagram_exists'] == 1:
        dataset['delta_use'] = convert_load_usage(dataset, varBackpack)
    if resample != 'no':
        dataset = resample_data(dataset, resolution=resample)
    dataset, varBackpack = update_dataset_backpack(dataset, varBackpack, resample)
    varBackpack = linear_regressors(dataset, varBackpack)
    opt_output = ewh_solver(dataset, varBackpack, optSolver=optSolver, solverPath=solverPath)

    return opt_output
