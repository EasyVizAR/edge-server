import time
import uuid


class HeadSet:
    def __init__(self, name, position, mapId):
        self.name = name
        self.position = {
            'x': position['x'],
            'y': position['y'],
            'z': position['z']
        }
        self.mapId = mapId
        self.lastUpdate = time.time()
        self.id = str(uuid.uuid4())


class Repository:
    headsets = {}

    def add_headset(self, name, position, mapId):
        headset = HeadSet(name, position, mapId)
        self.headsets[headset.id] = headset
        return headset.id

    def get_all_headsets(self):
        return self.headsets

    def get_headset(self, id):
        return self.headsets[id]

    def update_position(self, id, position):
        self.headsets[id].position['x'] = position['x']
        self.headsets[id].position['y'] = position['y']
        self.headsets[id].position['z'] = position['z']
        self.headsets[id].lastUpdate = time.time()


headset_repository = Repository()
