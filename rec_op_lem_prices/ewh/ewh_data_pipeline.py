from .ewh_flex import ewh_preparation
def ewh_varBackpack(paramsInput, dataset):

    ##############################################
    #             Data Preparation               #
    ##############################################

    # Select resample between 'no','15m','1h'
    varBackpack = ewh_preparation(paramsInput, dataset, resample='1h')

    return varBackpack
