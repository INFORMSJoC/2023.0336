import copy
import src.utils as utils
from .grid_state import GridState
from src.components import defaults
from src.components.electric_generators import WindTurbine, \
    SolarPhotovoltaicPanel, DieselGenerator
from src.components.energy_storage import Battery
from .energy_power import Energies

class Grid(object):

    _DIESEL_MIN = "diesel_min"
    _DIESEL_MAX = "diesel_max"
    _BATTERY_DISCHARGE = "battery_discharge"
    _BATTERY_CHARGE = "battery_charge"

    def __init__(self, generators=None, online_ratio=None, diesel_level=None):
        """Grid constructor __init__

        Keyword arguments:
        _generators    dictionary with generator types as key and lists as value
        _online_ratio  dictionary with generator id as key and % online as value
        _diesel_level  volume of fuel available
        _datetime      datetime object with current date and time
        """
        self._generators = generators if generators else dict()
        self._online_ratio = online_ratio
        self._diesel_level = diesel_level if diesel_level else 0.0
        self._available_power = {}

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'generators={self._generators!r},'
           f'online_ratio={self._online_ratio!r},'
           f'diesel_level={self._diesel_level!r})')

    def get_diesel_level(self):
        """Diesel level of grid"""
        return self._diesel_level

    def reset_fuel(self, fuel):
        """Set grid diesel reserves to input volume of fuel and reset
        diesel generator fuel consumption to 0.0"""
        if defaults.DIESEL_GENERATOR not in self._generators: return
        self._diesel_level = fuel
        for generator in self._generators[defaults.DIESEL_GENERATOR]:
            generator.reset_fuel_consumed()

    def reset_batteries(self):
        """Reset batteries to starting charge levels"""
        if defaults.BATTERY not in self._generators: return
        for battery in self._generators[defaults.BATTERY]:
            battery.reset_charge()

    def initialize_components(self, components_list):
        """Construct grid components from args"""
        for component in components_list:
            component_type = component.__class__.__name__
            if component_type in defaults.generator_types():
                if component_type not in self._generators:
                    self._generators[component_type] = []
                self._generators[component_type].append(component)
            else:
                raise ValueError("Component type not defined: "+str(component))

    def _fully_online_power(self, duration):
        """Power output dictionary of generators when fully functioning"""
        self._available_power = {}
        for type in self._generators:
            self._max_available_energy(
                type=type,
                duration=duration,
                fully_online=True,
            )

    def get_generator_dict(self):
        """Return generators"""
        return self._generators

    def get_generators(self):
        """Return list of generators"""
        generators = []
        for type in self._generators:
            for generator in self._generators[type]:
                generators.append(generator)
        return generators

    def generator_online_duration(self, generator, duration):
        """Duration scaled by % of current time-period input generator is available"""
        online_duration = duration * self._online_ratio[generator]
        return online_duration

    def update_current_conditions(self, timestep, weather):
        """Update weather, grid connnectivity, generator availability"""
        self._online_ratio = timestep.online_ratio()
        self._available_power = {}
        for type in self._generators:
            for generator in self._generators[type]:
                generator.update_current_conditions(timestep, weather)

    def _wet_stacking(self, power):
        """True if power will cause wet stacking
        SIMPLE HEURISTIC - COMPLICATED TO SOLVE FOR MULTIPLE GENERATORS
        """
        for generator in self._generators[defaults.DIESEL_GENERATOR]:
            if generator.wet_stacking(power): return True
        return False

    def _min_available_energy(self, type, duration, fully_online=False):
        """Available energy for an input type of component over an input duration"""
        if type not in self._generators: return 0.0
        supply = 0.0
        diesel_level = self._diesel_level
        for component in self._generators[type]:
            online_duration = self.generator_online_duration(
                generator=component,
                duration=duration,
            ) if not fully_online else duration
            if type == defaults.DIESEL_GENERATOR:
                fuel = min(
                    component.min_fuel_for_time(
                        duration=online_duration,
                    ),
                    self._diesel_level
                )
                if fuel > 0.0:
                    component.refill_fuel(fuel)
                    self._diesel_level -= fuel
            energy = component.min_available_energy(
                duration=online_duration,
            )
            if type == defaults.DIESEL_GENERATOR: component.remove_fuel(fuel)
            supply += energy
            self._available_power[component] = utils.average_power(
                energy=energy,
                duration=duration,
            )
        self._diesel_level = diesel_level
        return supply

    def _max_available_energy(self, type, duration, fully_online=False):
        """Available energy for an input type of component over an input duration"""
        if type not in self._generators: return 0.0
        supply = 0.0
        diesel_level = self._diesel_level
        for component in self._generators[type]:
            online_duration = self.generator_online_duration(
                generator=component,
                duration=duration,
            ) if not fully_online else duration
            if type == defaults.DIESEL_GENERATOR:
                fuel = min(
                    component.max_fuel_for_time(
                        duration=online_duration,
                    ),
                    self._diesel_level
                )
                if fuel > 0.0:
                    component.refill_fuel(fuel)
                    self._diesel_level -= fuel
            energy = component.max_available_energy(
                duration=online_duration,
            )
            if type == defaults.DIESEL_GENERATOR: component.remove_fuel(fuel)
            supply += energy
            self._available_power[component] = utils.average_power(
                energy=energy,
                duration=duration,
            )
        self._diesel_level = diesel_level
        return supply

    def _generate_energy(self, type, power, duration):
        """Generate energy from all generators of an input type over an input duration"""
        fuel_consumed = 0.0
        wet_stacking_flag = False
        supply = 0.0
        unmet_energy = utils.energy(power=power, duration=duration)
        for component in self._generators[type]:
            online_duration = self.generator_online_duration(
                generator=component,
                duration=duration
            )
            unmet_power = utils.average_power(
                energy=unmet_energy,
                duration=online_duration
            )
            if type == defaults.DIESEL_GENERATOR:
                fuel = min(
                    component.refill_required(
                        power=unmet_power,
                        duration=online_duration,
                    ),
                    self._diesel_level
                )
                if fuel > 0.0:
                    component.refill_fuel(fuel)
                    self._diesel_level -= fuel
                    fuel_consumed += fuel
                wet_stacking_flag = component.wet_stacking(unmet_power)
            energy = component.generate_energy(
                power=unmet_power,
                duration=online_duration,
            )
            unmet_energy -= energy
            supply += energy
            self._power_generation[component] = utils.average_power(
                energy=energy,
                duration=duration,
            )
            if (unmet_energy < defaults.EPSILON): break
        return supply, fuel_consumed, wet_stacking_flag

    def battery_capacity(self, duration):
        """Max energy that can be stored in all batteries over an input duration"""
        capacity = 0.0
        if defaults.BATTERY not in self._generators: return capacity
        for b in self._generators[defaults.BATTERY]:
            online_duration = self.generator_online_duration(
                generator=b,
                duration=duration
            )
            capacity += b.energy_capacity(
                duration=online_duration,
            )
        return capacity

    def store_battery_energy(self, power, duration):
        """Store energy to batteries"""
        unstored_energy = utils.energy(power=power, duration=duration)
        for b in self._generators[defaults.BATTERY]:
            online_duration = self.generator_online_duration(
                generator=b,
                duration=duration
            )
            unstored_power = utils.average_power(
                energy=unstored_energy,
                duration=online_duration,
            )
            energy = b.store_energy(
                power=unstored_power,
                duration=online_duration,
            )
            unstored_energy -= energy
            self._power_generation[b] = utils.average_power(
                energy=-1*energy,
                duration=duration,
            )
            if (unstored_energy < defaults.EPSILON): break
        return unstored_energy

    def _state_of_charge(self):
        """State of charge of aggregate BESS capacity"""
        if defaults.BATTERY not in self._generators or \
            len(self._generators[defaults.BATTERY]) == 0: return 0.0
        total_capacity = 0.0
        total_charge = 0.0
        for b in self._generators[defaults.BATTERY]:
            total_capacity += b._energy_rating
            total_charge += b._charge_level
        return total_charge / total_capacity

    def _energy_management_system_1(self, powers, previous_case):
        """Favor diesel to meet power load (legacy):
        Do not use diesel solely for the purpose of charging the battery energy storage system. 
        Use diesel when renewables cannot meet power load demands. 
        Discharge the battery energy storage system only when renewables and diesel 
        combined cannot meet power load demand."""
        load = powers[defaults.LOAD]
        photovoltaic = powers[defaults.PHOTOVOLTAIC_PANEL]
        wind = powers[defaults.WIND_TURBINE]
        diesel_max = powers[self._DIESEL_MAX]
        case = 4
        if load > 0:
            case = 0
        elif photovoltaic + wind + load >= 0:
            case = 1
        elif photovoltaic + wind + diesel_max + load >= 0:
            case = 3
        return case


    def _energy_management_system_2(self, powers, previous_case):
        """Favor battery energy storage system usage:
        Use battery energy storage system when renewables cannot meet power load demands.
        Continue to use diesel if battery is in the process of charging and diesel is on.
        Avoid diesel generator on/off switches.
        Avoid wet stacking when battery energy storage system is fully charged.
        """
        load = powers[defaults.LOAD]
        photovoltaic = powers[defaults.PHOTOVOLTAIC_PANEL]
        wind = powers[defaults.WIND_TURBINE]
        diesel_max = powers[self._DIESEL_MAX]
        battery_discharge = powers[self._BATTERY_DISCHARGE]
        battery_charge = powers[self._BATTERY_CHARGE]
        case = 4
        if load > 0:
            case = 0
        elif photovoltaic + wind + load >= 0:
            case = 1
            if photovoltaic + wind + load + battery_charge <= 0 and previous_case and previous_case == 3:
                case = 3 # continue running diesel to charge battery
        else:
            if photovoltaic + wind + battery_discharge + load >= 0 and \
                    (abs(battery_charge) < defaults.EPSILON or (previous_case and previous_case in [2,4])):
                case = 2 # use battery if fully charged or previously being used
            elif photovoltaic + wind + diesel_max + load >= 0:
                case = 3
            if case == 3: # avoid wet stacking
                if photovoltaic + wind + battery_discharge + load >= 0 and \
                    abs(battery_charge) < defaults.EPSILON \
                    and self._wet_stacking(power=load-photovoltaic-wind):
                    case = 2
        return case


    def _energy_management_system_3(self, powers, previous_case):
        """Favor diesel:
        Use diesel when renewables cannot meet power load demands
        or when battery energy storage system is not fully charged.
        Avoid diesel generator on/off switches.
        Avoid wet stacking when battery energy storage system is fully charged.
        """
        load = powers[defaults.LOAD]
        photovoltaic = powers[defaults.PHOTOVOLTAIC_PANEL]
        wind = powers[defaults.WIND_TURBINE]
        diesel_max = powers[self._DIESEL_MAX]
        battery_discharge = powers[self._BATTERY_DISCHARGE]
        battery_charge = powers[self._BATTERY_CHARGE]
        case = 4
        if load > 0:
            case = 0
        elif photovoltaic + wind + load >= 0:
            case = 1
            if photovoltaic + wind + load + battery_charge <= 0 and previous_case and previous_case in [3, 5]:
                case = 3 # continue running diesel to charge battery
        else:
            if photovoltaic + wind + diesel_max + load >= 0:
                case = 3
            elif photovoltaic + wind + battery_discharge + load >= 0:
                case = 2
            if case == 3 and previous_case and previous_case <= 2: # continue using battery
                if photovoltaic + wind + battery_discharge + load >= 0:
                    case = 2
            elif case == 3 and previous_case and previous_case >= 3: # continue running diesel
                if photovoltaic + wind + battery_discharge + load >= 0 and \
                    abs(battery_charge) < defaults.EPSILON \
                    and self._wet_stacking(power=load-photovoltaic-wind):
                    case = 2
        return case


    def _energy_management_system_4(self, powers, previous_case):
        """Maintain max state of charge:
        Use diesel when renewables cannot meet power load demands
        or when battery energy storage system is not fully charged.
        Discharge the battery energy storage system only when renewables and diesel 
        combined cannot meet power load demand."""
        load = powers[defaults.LOAD]
        photovoltaic = powers[defaults.PHOTOVOLTAIC_PANEL]
        wind = powers[defaults.WIND_TURBINE]
        diesel_max = powers[self._DIESEL_MAX]
        case = 4
        if load > 0:
            case = 0
        elif photovoltaic + wind + load >= 0:
            case = 1
        elif photovoltaic + wind + diesel_max + load >= 0:
            case = 3
        return case


    def operate(self, previous_case, load, duration, energy_management_system):
        """Generate power from all generating components over an input duration
        energy_management_system    string name of function to use

        case = 0       external power load supply, BESS charges
        case = 1       renewables meet power load, BESS charges
        case = 2       renewables and BESS meet power load, BESS discharges
        case = 3       renewables and diesel meet power load, BESS charges
        case = 4       all generators required, BESS discharges

        Step 1         identify case for current timestep
        Step 2         generate power (allow excess from renewable sources)
        Step 3         store battery power
        Step 4         return results
        """

        # Identify available power
        self._fully_online_power(duration)
        fully_online_power=dict()
        for key, value in self._available_power.items():
            fully_online_power[key] = copy.deepcopy(value)
        self._available_power = {}

        # Identify energy available, including upper and lower bounds
        energies = {}
        energies[defaults.LOAD] = - utils.energy(power=load, duration=duration)
        for i in [
            defaults.PHOTOVOLTAIC_PANEL,
            defaults.WIND_TURBINE,
        ]:
            energies[i] = self._max_available_energy(
                type=i,
                duration=duration,
            )
        energies[self._DIESEL_MIN] = self._min_available_energy(
            type=defaults.DIESEL_GENERATOR,
            duration=duration,
        )
        energies[self._DIESEL_MAX] = self._max_available_energy(
            type=defaults.DIESEL_GENERATOR,
            duration=duration,
        )
        energies[self._BATTERY_DISCHARGE] = self._max_available_energy(
            type=defaults.BATTERY,
            duration=duration,
        )
        energies[self._BATTERY_CHARGE] = - self.battery_capacity(duration)

        # identify case for current timestep
        powers = Energies(**energies).to_powers(duration)
        case = getattr(self, energy_management_system)(
            powers=powers,
            previous_case=previous_case,
        )

        # generation (do not allow excess from renewables)
        energy = energies[defaults.LOAD]
        if case >= 2: # use all renewables
            energy += energies[defaults.PHOTOVOLTAIC_PANEL]
            energy += energies[defaults.WIND_TURBINE]
        if case == 5:
            energy_battery = min(energies[self._BATTERY_DISCHARGE], max(0.0, -energy))
            energy_diesel = min(energies[self._DIESEL_MAX], max(0.0,-(energy+energy_battery)))
            if energy_diesel < energies[self._DIESEL_MIN]: # wet-stacking
                delta_diesel = energies[self._DIESEL_MIN] - energy_diesel
                delta_battery = min(energy_battery, delta_diesel)
                energy_battery -= delta_battery
                energy_diesel += delta_battery
        elif case == 4:
            energy_diesel = min(energies[self._DIESEL_MAX], max(0.0, -energy))
            energy_battery = min(energies[self._BATTERY_DISCHARGE], max(0.0, -(energy+energy_diesel)))
        elif case == 3:
            energy_diesel = min(energies[self._DIESEL_MAX], max(0.0, -(energy+energies[self._BATTERY_CHARGE])))
            energy_battery = min(-(energy+energy_diesel), 0.0)
        elif case == 2:
            energy_diesel = 0.0
            energy_battery = min(energies[self._BATTERY_DISCHARGE], max(0.0, -energy))
        elif case == 1:
            energy_diesel = 0.0
            energy += energies[self._BATTERY_CHARGE]
            renewable_priority = [defaults.PHOTOVOLTAIC_PANEL, defaults.WIND_TURBINE]
            energies[renewable_priority[0]] = min(energies[renewable_priority[0]], -1*energy) 
            energy += energies[renewable_priority[0]]
            if energy < 0.0:
                energies[renewable_priority[1]] = min(energies[renewable_priority[1]],-1*energy)
            else: energies[renewable_priority[1]] = 0.0
            energy += energies[renewable_priority[1]]
            energy_available_to_charge = energies[defaults.LOAD] + energies[defaults.WIND_TURBINE] \
                                            + energies[defaults.PHOTOVOLTAIC_PANEL]
            if energy_available_to_charge <= 0: energy_battery = 0.0
            else:
                energy_battery = max(energies[self._BATTERY_CHARGE], -1*energy_available_to_charge)
        elif case == 0:
            energy_diesel = 0.0
            energy_battery = energies[self._BATTERY_CHARGE]
        energies[defaults.DIESEL_GENERATOR] = energy_diesel
        energies[defaults.BATTERY] = energy_battery
        powers = Energies(**energies).to_powers(duration)

        # Step 2: generate power
        self._power_generation = {}
        fuel_consumed = 0
        wet_stacking_flag = False
        for type in self._generators:
            if powers[type] > 0.0:
                energy, fuel_consumed, wet_stacking_flag = self._generate_energy(
                    type=type,
                    power=powers[type],
                    duration=duration,
                )
            elif powers[type]<0.0 and type == defaults.BATTERY:
                unstored_energy = self.store_battery_energy(
                    power=-powers[defaults.BATTERY],
                    duration=duration,
                )
                if unstored_energy > defaults.EPSILON:
                    raise ValueError("Unstored energy error: "+str(unstored_energy))
            elif powers[type]<0.0:
                raise ValueError("Power is negative for type: "+(type, powers))

        # Step 4: return results
        return GridState(
            case=case,
            non_degraded_power=fully_online_power,
            available_power=self._available_power,
            power_generation=self._power_generation,
            state_of_charge=self._state_of_charge(),
            diesel_consumption = fuel_consumed,
            diesel_is_wet_stacking = wet_stacking_flag,
        )

    def _net_present_value(self, wacc, num_years, fuel_unit_cost, annual_use_factor):
        """Net present value of grid for an input weighted average cost of capital
        and over an input number of years in the planning horizon"""
        npv = 0.0
        for type in self._generators:
            for generator in self._generators[type]:
                npv += generator.investment_cost() / (1+wacc)
                npv += utils.net_present_value(
                    rate=wacc,
                    values=[generator.om_cost(fuel_unit_cost, annual_use_factor)
                            for i in range(num_years)],
                )
                npv -= generator.residual_value(num_years) / (1+wacc)**num_years
        return npv

    def update_components(self, ratings):
        """Use only for grid with exactly 1 DieselGenerator, 1 Battery
        and 1 PhotovoltaicPanel to update capacities, when rightsizing grid"""
        for component in [
            defaults.DIESEL_GENERATOR,
            defaults.BATTERY,
            defaults.PHOTOVOLTAIC_PANEL,
        ]:
            if component in self._generators and \
                len(self._generators[component]) == 1:
                self._generators[component][0].update(ratings[component])
            else:
                raise ValueError("Exactly 1 "+component+" is required in grid")

    def update_components_doe(self, initial_energy_resources, ratings):
        """Use initial_energy_resources"""
        self._generators = { k:v for k,v in initial_energy_resources.items() }
        for component in ratings:
            if len(self._generators[component]) > 1:
                raise ValueError("Exactly 1 "+component+" is required in grid")
            if ratings[component] == 0: self._generators.pop(component)
            else: self._generators[component][0].update(ratings[component])

    def lcoed(self, wacc, num_years, annual_energy, fuel_unit_cost, annual_use_factor):
        """Lifecycle Cost of Energy for Demand (LCOED) of grid for an input
        weighted average cost of capital, over an input number of years in the
        planning horizon, with an input annual energy use"""
        financial_npv = self._net_present_value(
            wacc=wacc,
            num_years=num_years,
            fuel_unit_cost=fuel_unit_cost,
            annual_use_factor=annual_use_factor,
        )
        energy_npv = utils.net_present_value(
            rate=wacc,
            values=[annual_energy for i in range(num_years)],
        )
        return financial_npv / energy_npv
