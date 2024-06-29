from datetime import timedelta

class TimePeriod(object):

    def __init__(self, start, end):
        """TimePeriod constructor __init__

        Keyword arguments:
        start     datetime object set to start of time period
        end       datetime object set to start of time period
        """
        self._start = start
        self._end = end
        self._duration = (end - start).total_seconds()/3600.0
        self._month = (start + (end - start)/2.0).strftime("%B") # use midpoint

    def start(self):
        return self._start

    def end(self):
        return self._end

    def duration(self):
        return self._duration

    def month(self):
        return self._month

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'start={self._start!r},'
           f'end={self._end!r},'
           f'duration={self._duration!r},'
           f'month={self._month!r})')
