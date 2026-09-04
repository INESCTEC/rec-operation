##############################################
##           Read Data Functions            ##
##############################################

import pandas as pd
import json
import sys

def read_data(paramsInput_filePath, dataset_filePath):
    # required data from user (prompted)
    with open(paramsInput_filePath) as json_data:
        paramsInput = json.load(json_data)

    if paramsInput['load_diagram_exists'] == 1:
        try:
            # read load diagram JSON
            dataset = pd.read_json(dataset_filePath, convert_dates=False)
        except:
            # read load diagram CSV
            dataset = pd.read_csv(dataset_filePath)
        # rename the two column
        dataset.columns = ['timestamp', 'load']
        # convert to datetime
        dataset['timestamp'] = pd.to_datetime(dataset['timestamp'], dayfirst=True, utc=True)

        ## verify minute resolution and missing data
        dataset = verify_1min_resolution(dataset)
    else:
        # read input water usage calendar
        with open(dataset_filePath) as json_data:
            dataset = json.load(json_data)

    ## verify if the data is larger than 1 month (43200 minutes)
    try:
        len(dataset) < 43500
    except:
        print("The file contains data with more than 30 days.\n")
        sys.exit(1)


    return dataset, paramsInput


def verify_1min_resolution(dataset):
    ## creates template from start and finish timestamps with minute resolution
    ## by joining the original dataset with this template, assures that all instances
    ## exists inside the final dataset. Missing values are fixed with 0.

    df = dataset.copy()
    # order by datetime
    df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
    # extract start date
    _start = df['timestamp'].iloc[0].strftime('%Y-%m-%d')
    # extract end date
    _end = df['timestamp'].iloc[-1].strftime('%Y-%m-%d 23:59')
    # create full length template, with 1-min res.
    _template = pd.DataFrame(pd.date_range(_start, _end, freq='min', tz='UTC'), columns=['timestamp'])
    # resample the original dataset to 1-min
    df = df.resample('1min', on='timestamp').sum().reset_index()
    # merge to the template
    df = _template.merge(df, how='left', left_on='timestamp', right_on='timestamp').fillna(0)
    # find average working value for fixing high values
    # delete observations with zero/ low values (<250W)
    _df = df.loc[df['load'] > 250]
    # calculate load threshold (1.25 times higher than the median)
    _threshold = 1.25*_df['load'].median()
    # delete observations where load is over threshold
    _df = _df.loc[df['load'] < _threshold]
    # estimated load is the median of the selected observations
    _median_load = _df['load'].median()
    # update threshold
    _threshold = 1.25 * _median_load
    # find the high values
    _outliers = df.loc[df['load'] > _threshold, 'load']

    # if there is outliers
    if len(_outliers) > 0:

        # for loop for finding aggregated values from missing measurements
        # with a missing value, the following should appear with the sum
        # of both. This loop finds the high value, and fix the attribution
        for idx_out in _outliers.index:
            # if it is the first value, replace immediately
            if idx_out == 0:
                df.loc[idx_out, 'load'] = _median_load
                continue

            # calculate the ratio between the outlier and the median
            _ratio = round(_outliers.loc[idx_out]/_median_load)
            # the ratio should cover at least 2 observations
            if _ratio < 2:
                _ratio = 2
            # calculate the new load value
            _new_load = round(_outliers.loc[idx_out] / _ratio)
            # start the empty block
            _block = 0
            # reverse loop starting from the previous value to find zeros blocks
            for i_all in reversed(range(0, idx_out)):
                # if there is no zero before, just replace and go to next outlier
                if (df.loc[i_all, 'load'] != 0) & (_block == 0):
                    df.loc[idx_out, 'load'] = _median_load
                    break
                # else start counting zeros
                if df.loc[i_all, 'load'] == 0:
                    _block += 1
                    # if block length the same or bigger than ratio, fill and continue
                    if _block >= _ratio:
                        df.loc[(idx_out - _ratio + 1):idx_out, 'load'] = _new_load
                        break
                    continue
                # block end detection
                if (df.loc[i_all, 'load'] != 0) & (_block != 0):
                    # if zero block size is >= _ratio, replace all block by median
                    if _block >= _ratio:
                        df.loc[(idx_out - _ratio + 1):idx_out, 'load'] = _new_load
                    else:
                        df.loc[(idx_out - _block):idx_out, 'load'] = _new_load
                    # close block
                    _block = 0
                    break

    return df

def data_space_parser(response, endpoint):
    # convert to dataframe
    df = pd.DataFrame(response.json()["data"])
    # convert to datetime
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    # make all seconds 0, for duplicate detection
    df['datetime'] = df['datetime'].apply(lambda t: t.replace(second=0))
    # remove duplicates
    df = df.drop_duplicates(subset='datetime', keep="last")
    # retain only necessary columns
    df = df[['datetime', 'value']]
    # rename the two column
    df.columns = ['timestamp', 'load']
    if endpoint == 'sel':
        # covert load from kWh to W
        df['load'] *= 60 * 1000
    return df
