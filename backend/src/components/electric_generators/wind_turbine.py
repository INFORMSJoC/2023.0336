from src.components import Generator, defaults

class WindTurbine(Generator):

    def __init__(self, id, power_rating, power_peak, cutin_speed, cutout_speed, rated_speed, height,
                    economic_lifespan, investment_cost, om_cost):
        """WindTurbine constructor __init__

        Arguments:
        id                      unique id for component
        power_rating            max power at standard test conditions
        power_peak              power at max wind       
        cutin_speed             wind turbine min wind speed required (m/s)
        cutout_speed            wind turbine max allowable wind speed (m/s)
        rated_speed             wind turbine min wind speed for max power delivery (m/s)
        height                  wind turbine height (m)
        economic_lifespan       number of years in economic life
        investment_cost         investment cost
        om_cost                 operating and maintenance cost/year (full usage)
        """
        self._id = id
        self._power_rating = power_rating
        self._power_peak = power_peak
        self._cutin_speed = cutin_speed
        self._cutout_speed = cutout_speed
        self._rated_speed = rated_speed
        self._height = height
        self._economic_lifespan = economic_lifespan
        self._investment_cost = investment_cost
        self._om_cost = om_cost

    @classmethod
    def init_from_database(cls, cls_dict):
        """WindTurbine class method reads dictionary from database info and calls constructor"""
        wt = cls(
            id = cls_dict["id"],
            power_rating = cls_dict["attributes"]["wt_power"],
            power_peak = cls_dict["attributes"]["wt_peak_power"],
            cutin_speed = cls_dict["attributes"]["wt_cutin_speed"],
            cutout_speed = cls_dict["attributes"]["wt_cutout_speed"],
            rated_speed = cls_dict["attributes"]["wt_rated_speed"],
            height = cls_dict["attributes"]["wt_height"],          
            economic_lifespan = cls_dict["attributes"]["wt_economic_lifespan"],
            investment_cost = cls_dict["attributes"]["wt_investment_cost"],
            om_cost = cls_dict["attributes"]["wt_om_cost"],
        )
        wt._validate_params()
        return wt

    def _validate_params(self):
        """Verify parameter values are in acceptable ranges"""
        if self._power_rating < defaults.EPSILON:
            raise ValueError("Wind turnbine size is too low, should be greater than 0")
        if self._power_peak < self._power_rating:
            raise ValueError("Wind turbine peak power is too low, should be at least equal to rated power")
        if self._cutin_speed < defaults.EPSILON:
            raise ValueError("Wind turbine cut-in speed is too low, should be at least 0")
        if self._rated_speed < self._cutin_speed:
            raise ValueError("Wind turbine rated speed is too low, should be at least cut-in speed")
        if self._cutout_speed < self._rated_speed:
            raise ValueError("Wind turbine cut-out speed is too low, should be at least rated speed")
        if self._height < 1.0 or self._height > 500.0:
            raise ValueError("Wind turbine height is not within expected range of 1 to 500 meters")

    def update(self, power_rating):
            self._power_rating = power_rating

    def _power(self):
        """Power generated
        Model references:
            Power Equation and Piecewise Function
                "Review of power curve modelling for wind turbines"
                (https://doi.org/10.1016/j.rser.2013.01.012)
                "Power Curve Modelling for Wind Turbines"
                (https://doi.org/10.1109/UKSim.2017.30)
                "Intelligent analysis of wind turbine power curve models"
                (https://doi.org/10.1109/CIASG.2014.7011548)
            Atmospheric Standard Conditions
                "Manual of the ICAO standard atmosphere" Doc 7488/3
                (https://standart.aero/en/icao/book/doc-7488-manual-of-the-icao-standard-atmosphere-extended-to-80-kilometres-262-500-feet-en-cons)
                (https://en.wikipedia.org/wiki/International_Standard_Atmosphere)
            Pressure and Temperature Adjustment for Wind Turbine Height
                "International Organization for Standardization ISO 2533:1975"
                (https://cdn.standards.iteh.ai/samples/7472/c203e9121d4c40e5bdc98844b1a1e2f4/ISO-2533-1975.pdf)
                (https://doi.org/10.5194/angeo-2019-88)
        """
        weather = self._current_weather
        if weather.wind_speed > self._cutin_speed and weather.wind_speed < self._cutout_speed:
            k = 2 # lower exponent may be more accurate than cubic textbook model according to citations
            fract_speed = ((weather.wind_speed**k - self._cutin_speed**k) \
                           / (self._rated_speed**k - self._cutin_speed**k))
        else:
            return 0.0 # skip computations if wind speed is not within operational limits
        pressure_o = 1013.25 # mbar
        temperature_o = 288.15 # kelvin
        celsius_to_kelvin = 273.15 # kelvin
        temperature_kelvin = weather.temperature + celsius_to_kelvin
        temperature_adjusted = temperature_kelvin - (6.5 * self._height)/1000.0
        pressure_adjusted = weather.pressure * ((1 - (0.0065 * self._height / temperature_kelvin))**5.255)
        fract_temp = temperature_adjusted / temperature_o
        fract_pressure = pressure_adjusted / pressure_o
        fract_density = (1 + fract_pressure) / (1 + fract_temp)
        power = min(self._power_rating * fract_density * fract_speed, self._power_peak)
        return power

    def _energy_output(self, duration):
        """Energy generated over an input duration of time"""
        energy_output = self._power() * duration
        return energy_output

    def _maintenance_time(self, duration_generation):
        """Maintenance time duration for input duration of generation time"""
        return duration_generation * (1-self._availability) / self._availability

    def _release(self, energy):
        """Output energy to grid (no action required for wind turbine)"""
        pass
