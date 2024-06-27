import json

MICROGRID_DESIGN_FILENAME = "microgrid-specifiction.json"
SIM_RESULTS_FILENAME = "sim.csv"
RUN_PREFIX = "run-"

def get_json_data(file):
    """Read data from json file"""
    with open(file, "rb") as file_object:
        doc = json.load(file_object)
    return doc

def get_profile(data, feature):
    """reorient month data"""
    map = {}
    for record in data:
        map[record["month"]] = record[feature]
    return map

def net_present_value(rate, values):
    """Net present value for input values discounted by input rate"""
    npv = 0.0
    for i in range(len(values)):
        npv += values[i] / (1+rate)**(i+1)
    return npv

def float_values(dictionary):
    for key, value in dictionary.items():
        try:
            dictionary[key] = float(value)
        except Exception:
            pass # do not raise error if value cannot be converted
    return dictionary

def get_dirname(diesel_val, photovoltaic_val, battery_val):
    return "dg"+str(int(diesel_val))+"_b"+str(int(battery_val))\
                +"_pv"+str(int(photovoltaic_val))
