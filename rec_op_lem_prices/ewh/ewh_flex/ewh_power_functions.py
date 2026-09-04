##############################################
##       EWH Power Profile Functions        ##
##############################################

import pandas as pd
import numpy as np
import math
import datetime

from .auxiliary_functions import round_up_hundred


##############################################
##          Create Usage Dataset            ##
##############################################
def create_usage_dataset(waterUsage):

    waterUsage = pd.DataFrame(waterUsage).copy()
    # create dataframe with the full minute resolution based on the
    firstUsage = pd.to_datetime(waterUsage.loc[0,'start']).strftime('%Y-%m-%d')
    lastUsage = pd.to_datetime(waterUsage.loc[len(waterUsage)-1,'start']).strftime('%Y-%m-%d')
    if firstUsage == lastUsage:
        lastUsage = (pd.to_datetime(lastUsage) + pd.DateOffset(days=1)).strftime('%Y-%m-%d')
    dataset = pd.DataFrame(pd.date_range(firstUsage, lastUsage, freq='min'), columns=['timestamp'])
    # delete last row (midnight of next day)
    dataset = dataset[:-1]
    # add delta_use column
    dataset['delta_use'] = 0

    # mark periods of usage
    for i in range(0,len(waterUsage)):
        _start = pd.to_datetime(waterUsage.loc[i,'start'])
        _duration = int(waterUsage.loc[i,'duration'])
        _end = _start + pd.DateOffset(minutes=_duration-1)
        _period = pd.date_range(_start, _end, freq='min')
        dataset.loc[dataset['timestamp'].isin(list(_period)),'delta_use'] = 1

    return dataset



##############################################
##         Real EWH Load Estimator          ##
##############################################
def real_ewh_load_estimator(dataset, varBackpack):

    # unpack some variables
    ewh_capacity = varBackpack['ewh_capacity']
    tempSet = varBackpack['tempSet']
    temp_inlet = varBackpack['temp_inlet']
    waterHeatCap = varBackpack['waterHeatCap']
    flow_rate_min = varBackpack['flow_rate_min']
    wh_init = varBackpack['wh_init']
    heatTransferCoeff = varBackpack['heatTransferCoeff']
    ewh_area = varBackpack['ewh_area']
    ambTemp = varBackpack['ambTemp']
    ewh_std_temp = varBackpack['ewh_std_temp']
    ewh_power = varBackpack['ewh_power']

    dataset = dataset[['timestamp','delta_use']].copy()

    # ewh starts off
    delta_in = 0
    # assumes 1min resolution
    delta_t = 1/60

    for t in range(len(dataset)):
        if t == 0:
            w_tot = wh_init
        else:
            w_water_prev = dataset.loc[t-1, 'w_water']
            w_in_prev = dataset.loc[t-1, 'w_in']
            w_loss_prev = dataset.loc[t-1, 'w_loss']
            w_tot = w_water_prev + w_in_prev - w_loss_prev

        temp = (w_tot * 3600 / (delta_t * 60)) / (ewh_capacity * waterHeatCap)
        ewh_flow = flow_rate_min * (tempSet-temp_inlet)/(temp-temp_inlet)
        delta_use = dataset.loc[t, 'delta_use']

        # guarantees that the ewh turns on when reaching 5ºC below working temperature
        # and turns off when reaching working temperature
        if (temp < (ewh_std_temp-3)):
            delta_in = 1
        if (temp >= ewh_std_temp):
            delta_in = 0

        # calculates stored energy after mixing water with inlet
        if delta_use == 1:
            if temp > tempSet:
                w_water = ((ewh_capacity-ewh_flow)*temp + ewh_flow*temp_inlet) * (waterHeatCap/3600)
            else:
                w_water = ((ewh_capacity-flow_rate_min)*temp + flow_rate_min*temp_inlet) * (waterHeatCap/3600)
        else:
            w_water = (temp * ewh_capacity * waterHeatCap / 3600)

        # calculate thermal losses
        w_loss = (heatTransferCoeff * ewh_area * ((temp - ambTemp)) * delta_t)

        # calculate input energy (on/off)
        w_in = ewh_power * delta_t * delta_in

        # fill variables in dataset
        dataset.loc[t, 'w_water'] = w_water
        dataset.loc[t, 'w_in'] = w_in
        dataset.loc[t, 'w_loss'] = w_loss
        dataset.loc[t, 'w_tot'] = w_tot
        dataset.loc[t, 'temp'] = temp
        dataset.loc[t, 'delta_in'] = delta_in
        dataset.loc[t, 'load'] = delta_in * ewh_power * 1000

    return dataset['load']



##############################################
##        EWH Spec Power Detection          ##
##############################################
def ewh_power_detection(dataset):
    _temp_load = pd.DataFrame(dataset.copy())
    _temp_load.columns = ['timestamp','load']
    _temp_load['timestamp'] = pd.to_datetime(_temp_load['timestamp'], utc=True)

    # delete observations where load is low
    _temp_load = _temp_load.loc[_temp_load['load'] > (0.15 * max(_temp_load['load'])/.95)]
    # filter out bottom and top 10% values
    _quantile = _temp_load['load'].quantile([0.1, 0.9])
    _temp_load = _temp_load[_temp_load['load'].between(_quantile[.1], _quantile[0.9])]
    # estimated load is the average of the selected observations
    _ewh_estimated_power = round_up_hundred(_temp_load['load'].mean()/.9)
    return _ewh_estimated_power



##############################################
##         Convert Load to Usage            ##
##############################################
def convert_load_usage(dataset, varBackpack):

    # unpack some variables
    ewh_power = varBackpack['ewh_power_original']
    ewh_max_temp = varBackpack['ewh_max_temp']
    temp_set = varBackpack['tempSet']

    # dataset copy
    _temp_load = pd.DataFrame(dataset.copy())
    _temp_load.columns = ['timestamp','load']
    _temp_load['timestamp'] = pd.to_datetime(_temp_load['timestamp'], utc=True)

    # required data
    ewh_power = 0.9 * ewh_power/1000  # kilowatts with 90% efficiency
    ewh_max_temp = 0.9 * ewh_max_temp # assumes 80% of max temperature
    temp_set = temp_set  # comfort temperature (usage)
    temp_inlet = 20  # network water temperature
    flow_out = 8.5  # liters per minute
    delta_t = 1 / 60  # minute resolution
    waterHeatCap = 4.186  # Specific heat capacity of water (4.186 J/g°C)

    # Total energy balance of prosumer’s EWH at the beginning (kWh)
    # w_init = ewh_max_temp * ewh_capacity * waterHeatCap / 3600
    # calculates approximate ewh flow with mixture with inlet water (assumes 90% of max temperature)
    # for tempSet=45 and for
    flow_ewh = flow_out * (temp_set - temp_inlet) / (ewh_max_temp - temp_inlet)
    # calculates losses
    # w_out = ewh_max_temp * (flow_ewh * TEMPO_USO) * waterHeatCap / 3600
    # calculates heating per minute
    w_in = ewh_power * delta_t

    # variable that flags EWH heating
    _temp_load['heating'] = 0
    _temp_load.loc[(_temp_load['load'] / 100) > (ewh_power / 5), 'heating'] = 1


    # 1st step: detect average duration of periods between automatic re-heating
    # objective, disregard periods where the EWH activates without water usage
    # auxiliary variable for flagging blanks blocks
    blank = 0
    # list of blank blocks duration
    blanks_list = list()
    for i in range(0, len(_temp_load)):
        if (_temp_load.loc[i, 'heating'] == 0) & (blank == 0):
            _start = _temp_load.loc[i, 'timestamp']
            blank = 1
            # flag instance as heating
            continue

        if (_temp_load.loc[i, 'heating'] == 1) & (blank == 1):
            _end = _temp_load.loc[i - 1, 'timestamp']
            blank = 0
            # calculate total minutes of blank
            blank_time = int((_end - _start).total_seconds() / 60)
            # only saves blocks if larger than 90min
            # if blank_time > 90:
            #     blanks_list.append(blank_time)
            blanks_list.append(blank_time)

    blanks_list = np.array(blanks_list)

    blank = 0
    heating = 0
    # variable that flags water usage
    _temp_load['usage'] = 0
    for i in range(0, len(_temp_load)):

        if (_temp_load.loc[i, 'heating'] == 0) & (blank == 0):
            _start_blank = _temp_load.loc[i, 'timestamp']
            blank = 1
            # flag instance as heating

        if (_temp_load.loc[i, 'heating'] == 1) & (blank == 1):
            _end_blank = _temp_load.loc[i - 1, 'timestamp']
            blank = 0
            # calculate total minutes of blank
            blank_time = int((_end_blank - _start_blank).total_seconds() / 60)


        if (_temp_load.loc[i, 'heating'] == 1) & (heating == 0):
            _start = _temp_load.loc[i, 'timestamp']
            heating = 1
            # flag instance as heating
            continue

        if (_temp_load.loc[i, 'heating'] == 0) & (heating == 1):
            _end = _temp_load.loc[i - 1, 'timestamp']
            heating = 0
            # calculate total minutes of heating
            heating_time = int((_end - _start).total_seconds() / 60)
            # calculate total minutes of usage via formula
            usage_time = heating_time / (1 + ((ewh_max_temp * flow_ewh * waterHeatCap) / (3600 * w_in)))
            # save float version
            usage_time_float = usage_time
            # save int/ceiled version
            usage_time = math.ceil(usage_time)
            # extract end of usage (subtract one, since start date already included)
            _end = _start + datetime.timedelta(minutes=(usage_time - 1))
            # only flags if blank is less than 90% of average, and higher than 1 min, or just higher than 2 min
            if ((blank_time < blanks_list.mean()*0.9) & (usage_time_float > 1)) | (usage_time_float > 2):
                # flag as using water
                _temp_load.loc[(_temp_load['timestamp'] >= _start) & (_temp_load['timestamp'] <= _end), 'usage'] = 1
            continue

    return _temp_load['usage']