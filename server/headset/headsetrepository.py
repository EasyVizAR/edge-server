import asyncio
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
from server.incidents.incident_handler import init_incidents_handler

headset_repository = None


class HeadSet:
    def __init__(self, name, position, mapId, id=None, lastUpdate=None, pose=None):

        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

        self.name = name
        self.mapId = mapId
        self.past_poses = []

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

        if lastUpdate is None:
            self.lastUpdate = time.time()
        else:
            self.lastUpdate = lastUpdate

        if pose is None:

            # add origin
            past_pos = {
                'position': self.position,
                'orientation': self.orientation,
                'time_stamp': self.lastUpdate
            }
            self.past_poses.append(past_pos)
        else:
            self.past_poses = pose

        # List of futures to resolve on the next headset update.
        self._headset_update_watchers = []

    def get_dir(self):
        return os.path.join(current_app.config['VIZAR_DATA_DIR'],
                            current_app.config['VIZAR_HEADSET_DIR'], self.id)

    def get_updates(self, after=0):
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
                    update['time'] = float(line[6])
                elif len(line) == 10:
                    update['orientation'] = {
                        "x": line[6],
                        "y": line[7],
                        "z": line[8]
                    }
                    update['time'] = float(line[9])
                else:
                    raise Exception("Unexpected line size ({}) in {}".format(len(line), updates_csv))

                if update['time'] >= after:
                    updates.append(update)

        return updates

    def get_past_poses(self, headset_id, incident):
        self.past_poses.clear()
        poses_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                      str(incident),
                                      current_app.config['VIZAR_HEADSET_DIR'], headset_id, "poses.csv")

        poses_file = open(poses_filepath, 'r')
        reader = csv.reader(poses_file)
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
            self.past_poses.append(past_pos)

        poses_file.close()
        return self.past_poses

    def notify_headset_update_watchers(self, update):
        for watcher in self._headset_update_watchers:
            if not watcher.cancelled():
                watcher.set_result(update)
        self._headset_update_watchers.clear()

    def wait_for_headset_update(self):
        future = asyncio.get_event_loop().create_future()
        self._headset_update_watchers.append(future)
        return future


class Repository:
    headsets = {}

    def __init__(self):

        # init incidents handler if it is not already
        self.incident_handler = init_incidents_handler(app=current_app)

        # save one headset to the headsets folder and one to the headsets folder in the incident
        headset_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'])
        incident_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                    str(self.incident_handler.current_incident),
                                    current_app.config['VIZAR_HEADSET_DIR'])

        os.makedirs(headset_dir, exist_ok=True)
        os.makedirs(incident_dir, exist_ok=True)

        for folder in os.scandir(headset_dir):
            if folder.is_dir():
                headset = json.load(open(f"{folder.path}/headset.json", 'r'))

                # read in past poses
                try:
                    poses_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                                    str(self.incident_handler.current_incident),
                                                    current_app.config['VIZAR_HEADSET_DIR'], str(headset['id']),
                                                    "poses.csv")

                    poses_file = open(poses_filepath, 'r')
                    reader = csv.reader(poses_file)
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

                    poses_file.close()
                    self.headsets[headset['id']] = HeadSet(headset['name'], headset['position'], headset['mapId'],
                                                           id=headset['id'], lastUpdate=headset['lastUpdate'],
                                                           pose=temp_history)
                except Exception as e:
                    # there is no past poses
                    self.headsets[headset['id']] = HeadSet(headset['name'], headset['position'], headset['mapId'],
                                                           id=headset['id'], lastUpdate=headset['lastUpdate'])

    def add_headset(self, name, position, mapId, id=None):
        headset = HeadSet(name, position, mapId, id=id)
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "headset.json")
        incident_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                         str(self.incident_handler.current_incident),
                                         current_app.config['VIZAR_HEADSET_DIR'], str(headset.id), "headset.json")

        headset_without_past_poses = {
            'id': headset.id,
            'name': headset.name,
            'mapId': headset.mapId,
            'position': headset.position,
            'orientation': headset.orientation,
            'lastUpdate': headset.lastUpdate
        }

        write_to_file(json.dumps(headset_without_past_poses, cls=GenericJsonEncoder), filepath)
        write_to_file(json.dumps(headset_without_past_poses, cls=GenericJsonEncoder), incident_filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        incident_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                         str(self.incident_handler.current_incident),
                                         current_app.config['VIZAR_HEADSET_DIR'], str(headset.id), "updates.csv")
        update_line = get_csv_line(
            [headset.id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
             headset.lastUpdate])

        append_to_file(update_line, filepath)
        append_to_file(update_line, incident_filepath)

        # create headset history file
        poses_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                      str(self.incident_handler.current_incident),
                                      current_app.config['VIZAR_HEADSET_DIR'], str(headset.id), "poses.csv")
        headset_poses = headset.past_poses
        new_line = get_csv_line([headset_poses[-1].get('position').get('x'),
                                 headset_poses[-1].get('position').get('y'),
                                 headset_poses[-1].get('position').get('z'),
                                 headset_poses[-1].get('orientation').get('x'),
                                 headset_poses[-1].get('orientation').get('y'),
                                 headset_poses[-1].get('orientation').get('z'),
                                 headset_poses[-1].get('time_stamp')])
        append_to_file(new_line, poses_filepath)

        self.headsets[headset.id] = headset
        return headset.id

    def get_all_headsets(self):
        for key in self.headsets:
            headset = self.headsets[key]
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
        headset.past_poses.append(past_pos)

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
        incident_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                         str(self.incident_handler.current_incident),
                                         current_app.config['VIZAR_HEADSET_DIR'],
                                         str(headset.id), 'headset.json')

        headset_without_past_poses = {
            'id': headset.id,
            'name': headset.name,
            'mapId': headset.mapId,
            'position': headset.position,
            'orientation': headset.orientation,
            'lastUpdate': headset.lastUpdate
        }

        write_to_file(json.dumps(headset_without_past_poses, cls=GenericJsonEncoder), filepath)
        write_to_file(json.dumps(headset_without_past_poses, cls=GenericJsonEncoder), incident_filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        incident_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                         str(self.incident_handler.current_incident),
                                         current_app.config['VIZAR_HEADSET_DIR'],
                                         str(headset.id), 'updates.csv')

        update_line = get_csv_line([id, headset.name, headset.mapId, position['x'], position['y'], position['z'],
                                    orientation['x'], orientation['y'], orientation['z'], headset.lastUpdate])

        append_to_file(update_line, filepath)
        append_to_file(update_line, incident_filepath)

        # write headset history to file
        poses_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                        str(self.incident_handler.current_incident),
                                        current_app.config['VIZAR_HEADSET_DIR'],
                                        str(headset.id), "poses.csv")
        new_line = get_csv_line([past_pos.get('position').get('x'), past_pos.get('position').get('y'),
                                 past_pos.get('position').get('z'), past_pos.get('orientation').get('x'),
                                 past_pos.get('orientation').get('y'),
                                 past_pos.get('orientation').get('z'), past_pos.get('time_stamp')])
        append_to_file(new_line, poses_filepath)

        update = {
            "headsetID": id,
            "position": position,
            "orientation": orientation,
            "mapID": None
        }

        headset.notify_headset_update_watchers(update)

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
        incident_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                         str(self.incident_handler.current_incident),
                                         current_app.config['VIZAR_HEADSET_DIR'],
                                         str(headset.id), 'headset.json')

        temp_headset = self.headsets[id]
        headset_without_past_poses = {
            'id': temp_headset.id,
            'name': temp_headset.name,
            'mapId': temp_headset.mapId,
            'position': temp_headset.position,
            'orientation': temp_headset.orientation,
            'lastUpdate': temp_headset.lastUpdate
        }

        write_to_file(json.dumps(headset_without_past_poses, cls=GenericJsonEncoder), filepath)
        write_to_file(json.dumps(headset_without_past_poses, cls=GenericJsonEncoder), incident_filepath)

        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], current_app.config['VIZAR_HEADSET_DIR'],
                                str(headset.id), "updates.csv")
        incident_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                         str(self.incident_handler.current_incident),
                                         current_app.config['VIZAR_HEADSET_DIR'],
                                         str(headset.id), 'updates.csv')

        update_line = get_csv_line(
            [headset_id, headset.name, headset.mapId, headset.position['x'], headset.position['y'],
             headset.position['z'],
             headset.orientation['x'], headset.orientation['y'], headset.orientation['z'], headset.lastUpdate])

        append_to_file(update_line, filepath)
        append_to_file(update_line, incident_filepath)

        return headset_id

    def remove_headset(self, headset_id):

        # check if headset exists
        if headset_id not in self.headsets:
            return False

        dir_path = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'headsets', str(headset_id))
        incident_path = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents',
                                     str(self.incident_handler.current_incident), 'headsets', str(headset_id))

        try:
            self.headsets.pop(headset_id)
            shutil.rmtree(dir_path)
            shutil.rmtree(incident_path)
        except OSError as e:
            print("Error in removing headset: %s : %s" % (dir_path, e.strerror))
            print("Error in removing headset: %s : %s" % (incident_path, e.strerror))
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
