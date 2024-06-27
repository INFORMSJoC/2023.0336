class TimePeriod(object):

    def __init__(self, start, mid, end):
        """TimePeriod constructor __init__

        Keyword arguments:
        start     datetime object set to start of time period
        mid       datetime object set to midpoint of time period
        end       datetime object set to end of time period
        """
        self._start = start
        self._mid = mid
        self._end = end
        self._duration = (end - start).total_seconds()/3600.0

    def start(self):
        return self._start

    def mid(self):
        return self._mid

    def end(self):
        return self._end

    def duration(self):
        return self._duration

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'start={self._start!r},'
           f'mid={self._mid!r},'
           f'end={self._end!r},'
           f'duration={self._duration!r},')
