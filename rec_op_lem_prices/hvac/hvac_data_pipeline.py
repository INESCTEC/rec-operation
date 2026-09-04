from .hvac_flex import hvac_preparation

def hvac_varBackpack(paramsInput, dataset):
    """
    Prepares HVAC data similar to the EWH approach.
    - Selects time resampling: 'no', '15m', '1h'
    - Calls `hvac_preparation()` for data processing
    """
    varBackpack = hvac_preparation(paramsInput, dataset, resample='1h')
    return varBackpack
