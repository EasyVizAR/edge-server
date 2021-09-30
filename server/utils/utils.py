from json import JSONEncoder


class GenericJsonEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__