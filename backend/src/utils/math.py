import math

def sin(degrees):
    """input angle in degrees"""
    return math.sin(math.radians(degrees))

def cos(degrees):
    """input angle in degrees"""
    return math.cos(math.radians(degrees))

def tan(degrees):
    """input angle in degrees"""
    return math.tan(math.radians(degrees))

def arcsin(x):
    """return angle in degrees"""
    return math.degrees(math.asin(x))

def arccos(x):
    """return angle in degrees"""
    return math.degrees(math.acos(x))

def arctan2(y,x):
    """return angle in degrees"""
    return math.degrees(math.atan2(y,x))
