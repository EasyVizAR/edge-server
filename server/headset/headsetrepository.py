import json
import time
import uuid

from quart import current_app

from server.utils.utils import *
from server.utils.utils import GenericJsonEncoder

headset_repository = None


class HeadSet:
    def __init__(self, name, position, mapId, id=None, lastUpdate=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.mapId = mapId
        self.position = {
            'x': position['x'],
            'y': position['y'],
            'z': position['z']
        }
        if lastUpdate is None:
            self.lastUpdate = time.time()
        else:
            self.lastUpdate = lastUpdate


class Repository:
    headsets = {}

    def __init__(self):
        headset_dir = f"{current_app.config['VIZAR_DATA_DIR']}{current_app.config['VIZAR_HEADSET_DIR']}"
        for folder in os.scandir(headset_dir):
            if folder.is_dir():
                headset = json.load(open(f"{folder.path}/headset.json", 'r'))
                self.headsets[headset['id']] = HeadSet(headset['name'], headset['position'], headset['mapId'],
                                                       id=headset['id'], lastUpdate=headset['lastUpdate'])

    def add_headset(self, name, position, mapId):
        headset = HeadSet(name, position, mapId)
        filepath = f"{current_app.config['VIZAR_DATA_DIR']}{current_app.config['VIZAR_HEADSET_DIR']}{headset.id}" \
                   f"/headset.json"
        write_to_file(json.dumps(headset, cls=GenericJsonEncoder), filepath)

        filepath = f"{current_app.config['VIZAR_DATA_DIR']}{current_app.config['VIZAR_HEADSET_DIR']}{headset.id}/updates.csv"
        update_line = get_csv_line(
            [headset.id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
             headset.lastUpdate])
        append_to_file(update_line, filepath)

        self.headsets[headset.id] = headset
        return headset.id

    def get_all_headsets(self):
        return self.headsets

    def get_headset(self, id):
        if id not in self.headsets:
            return None
        return self.headsets[id]

    def update_position(self, id, position):
        if id not in self.headsets:
            return None
        self.headsets[id].position['x'] = position['x']
        self.headsets[id].position['y'] = position['y']
        self.headsets[id].position['z'] = position['z']
        self.headsets[id].lastUpdate = time.time()

        headset = self.headsets[id]

        filepath = f"{current_app.config['VIZAR_DATA_DIR']}{current_app.config['VIZAR_HEADSET_DIR']}{headset.id}/" \
                   f"headset.json"
        write_to_file(json.dumps(headset, cls=GenericJsonEncoder), filepath)

        filepath = f"{current_app.config['VIZAR_DATA_DIR']}{current_app.config['VIZAR_HEADSET_DIR']}{id}/updates.csv"
        update_line = get_csv_line([id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
                                    headset.lastUpdate])
        append_to_file(update_line, filepath)

        return headset

    # TODO: Will this have a separate
    def create_image(self, intent, data, type):
        id = str(uuid.uuid4())
        img_type = type.split("/")[1]
        url = f"{current_app.config['IMAGE_UPLOADS']}{id}.{img_type}"
        return {'id': id, 'url': url, 'intent': intent, 'data': data, 'type': type}


def get_headset_repository():
    global headset_repository
    if headset_repository is None:
        headset_repository = Repository()
    return headset_repository
