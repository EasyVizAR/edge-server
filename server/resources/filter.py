import operator


class Filter:
    def __init__(self):
        self.conditions = []

    def add(self, field, value, op):
        self.conditions.append((field, value, op))

    def add_from_dict(self, d):
        for key, value in d.items():
            if value is not None:
                self.target_equal_to(key, value)

    def target_equal_to(self, field, value):
        self.add(field, value, operator.eq)

    def target_greater_than(self, field, value):
        self.add(field, value, operator.gt)

    def target_less_than(self, field, value):
        self.add(field, value, operator.lt)

    def matches(self, item):
        for field, value, op in self.conditions:
            if not op(getattr(item, field), value):
                return False
        return True
