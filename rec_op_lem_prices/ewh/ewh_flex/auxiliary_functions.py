import datetime

##############################################
##           Auxiliary Functions            ##
##############################################

def fillDefaults(paramsInput, paramsDefault):
    result = paramsInput.copy()  # Create a copy to avoid modifying the original dictionary

    for key, default_value in paramsDefault.items():
        if isinstance(default_value, dict):
            # If the value is a nested dictionary, recursively fill in default values
            result[key] = fillDefaults(result.get(key, {}), default_value)
        else:
            # Otherwise, fill in the default value only if the key is missing
            result.setdefault(key, default_value)

    return result

def create_empty_nested_dict(keys):
    result = {key: {} for key in keys}
    return result

def round_up_hundred(x):
    x -= x % -100
    return x




##############################################
##      Streamlit Auxiliary Functions       ##
##############################################

# timestamp format validator
def is_valid_time_format(input_str):
    try:
        # Attempt to parse the input string as a datetime object
        time_obj = datetime.datetime.strptime(input_str, '%H:%M')

        # Check if the hour and minute values are within valid ranges
        if 0 <= time_obj.hour < 24 and 0 <= time_obj.minute < 60:
            return True
        else:
            return False
    except ValueError:
        # If parsing fails, the input string is not in the correct format
        return False



