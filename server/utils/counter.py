import time


class Counter:
    """
    Count events and produce rates over a time window.

    For example, this can be used to count bytes sent or received and produce
    an average rate of bytes/second.
    """
    def __init__(self, name="received", unit="bytes", max_buffer_len=24, weight=0.95):
        self.name = name
        self.unit = unit
        self.max_buffer_len = max_buffer_len
        self.weight = weight

        t = time.time()
        self.times = [t]
        self.values = [0]

        self.total_count = 0
        self.total_value = 0

    def add(self, value, t=None):
        if t is None:
            t = time.time()

        if len(self.values) >= self.max_buffer_len:
            self.times.pop(0)
            self.values.pop(0)

        self.times.append(t)
        self.values.append(value)

        self.total_count += 1
        self.total_value += value

    def dump(self):
        tdiff = time.time() - self.times[0]
        messages_per_second = len(self.values) / tdiff
        units_per_second = sum(self.values) / tdiff

        return {
            "messages_{}".format(self.name): self.total_count,
            "{}_{}".format(self.unit, self.name): self.total_value,
            "messages_{}_per_second".format(self.name): messages_per_second,
            "{}_{}_per_second".format(self.unit, self.name): units_per_second,
            "last_{}_time".format(self.name): self.times[-1]
        }
