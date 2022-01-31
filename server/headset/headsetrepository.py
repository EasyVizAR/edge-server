import csv
import json
import os
import time
import uuid
import shutil

from quart import current_app

from server.maps.maprepository import get_map_repository
from server.utils.utils import *
from server.utils.utils import GenericJsonEncoder

headset_repository = None


class HeadSet:
    def __init__(self, name, position, mapId, id=None, lastUpdate=None, history=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.mapId = mapId
        self.position_history = []

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

        if history is None:

            # add origin
            past_pos = {
                'position': self.position,
                'orientation': self.orientation,
                'time_stamp': self.lastUpdate
            }
            self.position_history.append(past_pos)
        else:
            self.position_history = history

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

    def get_history(self):
        return self.position_history


class Repository:
    headsets = {}

    def __init__(self):
        headset_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'])
        os.makedirs(headset_dir, exist_ok=True)
        for folder in os.scandir(headset_dir):
            if folder.is_dir():
                headset = json.load(open(f"{folder.path}/headset.json", 'r'))

                # read in history
                try:
                    filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'],
                                            current_app.config['VIZAR_HEADSET_DIR'], str(headset['id']), "history.csv")

                    history_file = open(filepath, 'r')
                    reader = csv.reader(history_file)
                    temp_history = []
                    for line in reader:
                        past_pos = {
                            'position': {
                                'x': line[0],
                                'y': line[1],
                                'z': line[2]
                            },
                            'orientation': {
                                'x': line[3],
                                'y': line[4],
                                'z': line[5]
                            },
                            'time_stamp': line[6]
                        }
                        temp_history.append(past_pos)

                    history_file.close()
                    self.headsets[headset['id']] = HeadSet(headset['name'], headset['position'], headset['mapId'],
                                                           id=headset['id'], lastUpdate=headset['lastUpdate'],
                                                           history=temp_history)
                except Exception as e:
                    # there is no history
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

        # create headset history file
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "history.csv")
        headset_history = headset.position_history
        new_line = get_csv_line([headset_history.get('position').get('x'), headset_history.get('position').get('y'),
                                 headset_history.get('position').get('z'), headset_history.get('orientation').get('x'),
                                 headset_history.get('orientation').get('y'),
                                 headset_history.get('orientation').get('z'), headset_history.get('time_stamp')])
        append_to_file(new_line, filepath)

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

        update_time = time.time()
        headset = self.headsets[id]

        # first save current position to history
        past_pos = {
            'position': {
                'x': position['x'],
                'y': position['y'],
                'z': position['z']
            },
            'orientation': {
                'x': orientation['x'],
                'y': orientation['y'],
                'z': orientation['z']
            },
            'time_stamp': update_time
        }
        headset.position_history.append(past_pos)

        # then update current position
        headset.position['x'] = position['x']
        headset.position['y'] = position['y']
        headset.position['z'] = position['z']
        headset.orientation['x'] = orientation['x']
        headset.orientation['y'] = orientation['y']
        headset.orientation['z'] = orientation['z']
        headset.lastUpdate = update_time

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), 'headset.json')

        headset_without_history = {
            'id': id,
            'name': headset.name,
            'mapId': headset.mapId,
            'position': headset.position,
            'orientation': headset.orientation,
            'pixelPosition': headset.pixelPosition,
            'lastUpdate': headset.lastUpdate
        }

        write_to_file(json.dumps(headset_without_history, cls=GenericJsonEncoder), filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        update_line = get_csv_line([id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
                                    orientation['x'], orientation['y'], orientation['z'], headset.lastUpdate])
        append_to_file(update_line, filepath)

        # write headset history to file
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "history.csv")
        new_line = get_csv_line([past_pos.get('position').get('x'), past_pos.get('position').get('y'),
                                 past_pos.get('position').get('z'), past_pos.get('orientation').get('x'),
                                 past_pos.get('orientation').get('y'),
                                 past_pos.get('orientation').get('z'), past_pos.get('time_stamp')])
        append_to_file(new_line, filepath)

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
        temp_headset = self.headsets[id]
        headset_without_history = {
            'id': id,
            'name': temp_headset.name,
            'mapId': temp_headset.mapId,
            'position': temp_headset.position,
            'orientation': temp_headset.orientation,
            'pixelPosition': temp_headset.pixelPosition,
            'lastUpdate': temp_headset.lastUpdate
        }
        write_to_file(json.dumps(headset_without_history, cls=GenericJsonEncoder), filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        update_line = get_csv_line(
            [headset_id, headset.name, headset.mapId, headset.position['x'], headset.position['y'],
             headset.position['z'],
             headset.orientation['x'], headset.orientation['y'], headset.orientation['z'], headset.lastUpdate])
        append_to_file(update_line, filepath)

        return headset_id

    def remove_headset(self, headset_id):
        # check if headset exists
        if headset_id not in self.headsets:
            return False

        dir_path = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'headsets/', str(headset_id))
        try:
            self.headsets.pop(headset_id)
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error in removing headset: %s : %s" % (dir_path, e.strerror))
            return False

        return True


def get_headset_repository():
    global headset_repository
    if headset_repository is None:
        headset_repository = Repository()

    # Create a Test headset with ID 0 for use while the HoloLens app is in development.
    # Remove this code after headset registration is working reliably.
    if headset_repository.get_headset("0") is None:
        headset_repository.add_headset("Test", {"x": 0.0, "y": 0.0, "z": 0.0}, "0", id="0")

    return headset_repository
