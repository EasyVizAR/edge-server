class PoolLimiter:
    """
    Simulate the behavior of a work queue in order to avoid submitting
    duplicate tasks.
    """
    def __init__(self):
        self.active = set()

    def try_submit(self, key):
        if key in self.active:
            return False
        else:
            self.active.add(key)
            return True

    def finished(self, key):
        if key in self.active:
            self.active.remove(key)
