import pandas as pd

def hvac_preparation(paramsInput, dataset, resample='no'):
    """
    Prepares HVAC input data for optimization, similar to EWH preprocessing.
    """
    dataset = pd.DataFrame(dataset).copy()

    # Default HVAC parameters
    hvac_defaults = {
        "hvac_capacity": 3.0,  # Max Power (kW)
        "efficiency": 0.9,  # HVAC Efficiency
        "temp_min": 20.0,  # Min Allowed Temp (°C)
        "temp_max": 24.0,  # Max Allowed Temp (°C)
        "init_temp": 22.0,  # Initial Room Temp (°C)
    }

    # Fill missing values with defaults
    paramsInput.setdefault("hvac_specs", hvac_defaults)

    # Extract HVAC settings
    hvac_capacity = paramsInput["hvac_specs"]["hvac_capacity"]
    efficiency = paramsInput["hvac_specs"]["efficiency"]
    temp_min = paramsInput["hvac_specs"]["temp_min"]
    temp_max = paramsInput["hvac_specs"]["temp_max"]
    init_temp = paramsInput["hvac_specs"]["init_temp"]

    # Resample dataset if needed
    if resample != 'no':
        dataset = dataset.resample(resample, on='timestamp').mean()

    # Store HVAC data in varBackpack
    varBackpack = {
        "hvac_capacity": hvac_capacity,
        "efficiency": efficiency,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "init_temp": init_temp,
        #"dataset": dataset.to_dict('records')
    }

    return varBackpack
