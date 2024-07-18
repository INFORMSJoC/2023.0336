import src.utils as utils

class Powers(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_energies(self, duration):
        items = [(a, getattr(self, a)) for a in dir(self) if not a.startswith("_")
                            and not callable(getattr(self,a))]
        energies = {
            attr:utils.average_power(val, duration) if val != None else None
            for attr, val in items if attr != "self"
        }
        return energies

class Energies(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_powers(self, duration):
        items = [(a, getattr(self, a)) for a in dir(self) if not a.startswith("_")
                            and not callable(getattr(self,a))]
        powers = {
            attr:utils.average_power(val, duration) if val != None else None
            for attr, val in items if attr != "self"
        }
        return powers
