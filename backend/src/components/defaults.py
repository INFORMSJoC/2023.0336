EPSILON = .000001 # for numerical stability

"""Class names are to define generator types"""
WIND_TURBINE = "WindTurbine"
DIESEL_GENERATOR = "DieselGenerator"
PHOTOVOLTAIC_PANEL = "SolarPhotovoltaicPanel"
BATTERY = "Battery"

"""Names for other power references"""
LOAD = "Powerload"

def generator_types():
    """List of generator types"""
    return [ WIND_TURBINE, DIESEL_GENERATOR, \
        PHOTOVOLTAIC_PANEL, BATTERY ]

def renewable_generator_types():
    """List of renewable generator types"""
    return [ WIND_TURBINE, PHOTOVOLTAIC_PANEL ]
