import time


class TokenBucket:
    def __init__(self, capacity=10.0, rate=1.0):
        self.capacity = capacity
        self.rate = rate

        self.last_update = time.time()
        self.value = capacity

    def check(self, amount=1.0):
        if self.value >= amount:
            return True

        now = time.time()
        value = self.value + self.rate * (now - self.last_update)

        self.value = min(value, self.capacity)
        self.last_update = now

        return self.value >= amount

    def drain(self, amount=1.0):
        self.value -= amount

    def update_rate(self, new_rate, weight=0.5):
        """
        Update fill rate using new value and exponential moving average.
        """
        self.rate = weight * new_rate + (1.0-weight) * self.rate
