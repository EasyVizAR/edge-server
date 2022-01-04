import csv
import json
import os
import time
import uuid

from quart import current_app

from server.maps.maprepository import get_map_repository
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
        self.orientation = {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
        self.pixelPosition = {
            "x": None,
            "y": None
        }
        if lastUpdate is None:
            self.lastUpdate = time.time()
        else:
            self.lastUpdate = lastUpdate

    def get_dir(self):
        return os.path.join(current_app.config['VIZAR_DATA_DIR'],
                            current_app.config['VIZAR_HEADSET_DIR'], self.id)

    def get_updates(self):
        headset_dir = self.get_dir()
        updates_csv = os.path.join(headset_dir, "updates.csv")

        updates = []
        if not os.path.exists(updates_csv):
            return updates

        with open(updates_csv, "r") as source:
            reader = csv.reader(source)
            for line in reader:
                update = {
                    "mapId": line[2],
                    "position": {
                        "x": line[3],
                        "y": line[4],
                        "z": line[5]
                    }
                }

                if len(line) == 7:
                    update['time'] = line[6]
                elif len(line) == 10:
                    update['orientation'] = {
                        "x": line[6],
                        "y": line[7],
                        "z": line[8]
                    }
                    update['time'] = line[9]
                else:
                    raise Exception("Unexpected line size ({}) in {}".format(len(line), updates_csv))

                updates.append(update)

        return updates


class Repository:
    headsets = {}

    def __init__(self):
        headset_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'])
        os.makedirs(headset_dir, exist_ok=True)
        for folder in os.scandir(headset_dir):
            if folder.is_dir():
                headset = json.load(open(f"{folder.path}/headset.json", 'r'))
                self.headsets[headset['id']] = HeadSet(headset['name'], headset['position'], headset['mapId'],
                                                       id=headset['id'], lastUpdate=headset['lastUpdate'])

    def add_headset(self, name, position, mapId, id=None):
        headset = HeadSet(name, position, mapId, id=id)
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "headset.json")
        write_to_file(json.dumps(headset, cls=GenericJsonEncoder), filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        update_line = get_csv_line(
            [headset.id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
             headset.lastUpdate])
        append_to_file(update_line, filepath)

        self.headsets[headset.id] = headset
        return headset.id

    def get_all_headsets(self):
        for key in self.headsets:
            headset = self.headsets[key]
            if get_map_repository().get_map(headset.mapId) is not None:
                intrinsic = get_map_repository().get_map(headset.mapId).intrinsic
                extrinsic = get_map_repository().get_map(headset.mapId).extrinsic
                if intrinsic is not None and extrinsic is not None:
                    pixels = get_pixels(extrinsic, intrinsic,
                                        [headset.position['x'], headset.position['y'], headset.position['z']])
                    headset.pixelPosition['x'] = pixels[0]
                    headset.pixelPosition['y'] = pixels[1]
        return list(self.headsets.values())

    def get_headset(self, id):
        if id not in self.headsets:
            return None
        return self.headsets[id]

    def update_pose(self, id, position, orientation):
        if id not in self.headsets:
            return None
        self.headsets[id].position['x'] = position['x']
        self.headsets[id].position['y'] = position['y']
        self.headsets[id].position['z'] = position['z']
        self.headsets[id].orientation['x'] = orientation['x']
        self.headsets[id].orientation['y'] = orientation['y']
        self.headsets[id].orientation['z'] = orientation['z']
        self.headsets[id].lastUpdate = time.time()

        headset = self.headsets[id]

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "headset.json")
        write_to_file(json.dumps(headset, cls=GenericJsonEncoder), filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        update_line = get_csv_line([id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
                                    orientation['x'], orientation['y'], orientation['z'], headset.lastUpdate])
        append_to_file(update_line, filepath)

        update = {
            "headsetID": id,
            "position": position,
            "orientation": orientation,
            "mapID": None
        }

        return update

    def update_position(self, id, position):
        orientation = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        return self.update_pose(id, position, orientation)

    def update_headset_name(self, headset_id, name):

        # check if headset exists
        if headset_id not in self.headsets:
            return None

        # update the headset name
        self.headsets[headset_id].name = name

        headset = self.headsets[headset_id]

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "headset.json")
        write_to_file(json.dumps(headset, cls=GenericJsonEncoder), filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        update_line = get_csv_line([headset_id, headset.name, headset.mapId, headset.position['x'], headset.position['y'], headset.position['z'],
                                    headset.orientation['x'], headset.orientation['y'], headset.orientation['z'], headset.lastUpdate])
        append_to_file(update_line, filepath)

        return headset_id


def get_headset_repository():
    global headset_repository
    if headset_repository is None:
        headset_repository = Repository()

    # Create a Test headset with ID 0 for use while the HoloLens app is in development.
    # Remove this code after headset registration is working reliably.
    if headset_repository.get_headset("0") is None:
        headset_repository.add_headset("Test", {"x": 0.0, "y": 0.0, "z": 0.0}, "0", id="0")

    return headset_repository
