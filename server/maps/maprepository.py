import json
import os
import uuid
import shutil

import numpy as np
from quart import current_app

from server.utils.utils import GenericJsonEncoder, write_to_file, get_pixels, get_vector
from server.incidents.incident_handler import init_incidents_handler

map_repository = None


class Map:
    def __init__(self, name, image='', incident=-1, id=None, viewBox=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.image = image
        self.incident = incident

        if viewBox is None:
            self.viewBox = dict(left=0, top=0, width=0, height=0)
        else:
            self.viewBox = viewBox

    def __str__(self):
        return "id=" + self.id + ", name=" + self.name + ", image=" + str(self.image)

    def save(self):
        path = os.path.join(get_map_repository().get_base_dir(), self.id, "map.json")
        with open(path, "w") as output:
            output.write(json.dumps(self, cls=GenericJsonEncoder))


class Feature:
    def __init__(self, name, mapId, style, id=None, position=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        if position is not None:
            self.position = {
                'x': position['x'],
                'y': position['y'],
                'z': position['z']
            }
        else:
            self.position = {
                'x': None,
                'y': None,
                'z': None
            }
        self.mapId = mapId
        self.style = {
            "placement": style['placement'],
            "topOffset": style['topOffset'],
            "leftOffset": style['leftOffset'],
            "icon": style['icon']
        }


class Repository:
    maps = {}
    features = {}

    def __init__(self, app=current_app):
        self.app_config = app.config

        # init incidents handler if it is not already
        self.incident_handler = init_incidents_handler(app=app)

        map_dir = self.get_base_dir()
        os.makedirs(map_dir, exist_ok=True)

        for folder in os.scandir(map_dir):
            if folder.is_dir():
                map = json.load(open(f"{folder.path}/map.json", 'r'))
                image = None
                viewBox = None
                if 'viewBox' in map:
                    viewBox = map['viewBox']
                if 'image' in map:
                    image = map['image']
                self.maps[map['id']] = Map(map['name'], image, viewBox=viewBox, id=map['id'])

                feature_filename = f"{folder.path}/features.json"
                features = []
                try:
                    features = json.load(open(feature_filename, 'r'))
                    if not isinstance(features, list):
                        print("Warning: map features file {} is malformed".format(feature_filename))
                        features = []
                except json.decoder.JSONDecodeError:
                    print("Error reading {}".format(feature_filename))
                    features = []

                feature_list = []
                if len(features) > 0:
                    for feature in features:
                        print(feature.keys())
                        feature_obj = Feature(feature['name'], feature['mapId'], feature['style'],
                                              id=feature['id'], position=feature['position'])
                        feature_list.append(feature_obj)
                self.features[map['id']] = feature_list

    def create_image(self, intent, data, type, viewBox=None):
        intentId = data['mapID'] if 'maps' == intent else str(uuid.uuid4())
        img_type = "svg" if type.split("/")[1] == "svg+xml" else type.split("/")[1]
        url = f"{current_app.config['IMAGE_UPLOADS']}{intentId}.{img_type}"
        if intent == 'maps' and viewBox is not None:
            self.maps[intentId].viewBox = viewBox
            filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/',
                                    str(intentId), "map.json")
            write_to_file(json.dumps(self.maps[intentId], cls=GenericJsonEncoder), filepath)

        return {'id': intentId, 'url': url, 'intent': intent, 'data': data, 'type': type, 'viewBox': viewBox}

    def add_feature(self, id, name, mapId, style, position=None):
        if mapId not in self.maps.keys():
            return None

        feature = Feature(name, mapId, style, id=id)

        if position is not None:
            feature.position['x'] = position['x']
            feature.position['y'] = position['y']
            feature.position['z'] = position['z']

        map_features = []
        if mapId in self.features:
            map_features = self.features[mapId]

        map_features.append(feature)
        filepath = os.path.join(self.get_base_dir(), str(feature.mapId), "features.json")
        write_to_file(json.dumps(map_features, cls=GenericJsonEncoder), filepath)
        self.features[mapId] = map_features
        return feature

    def get_map_features(self, mapId):
        if mapId not in self.features.keys():
            return None
        return self.features[mapId]

    def add_map(self, id, name, image, viewBox=None):
        map = Map(name, image, incident=self.incident_handler.current_incident, id=id, viewBox=viewBox)
        filepath = os.path.join(self.get_base_dir(), str(map.id), "map.json")
        write_to_file(json.dumps(map, cls=GenericJsonEncoder), filepath)
        filepath = os.path.join(self.get_base_dir(), str(map.id), "features.json")
        write_to_file('[]', filepath)
        self.maps[map.id] = map
        return map.id

    def replace_map(self, id, name, image):
        if id not in self.maps.keys():
            return None

        id = self.add_map(id, name, image)
        return id

    def remove_map(self, map_id):
        if map_id not in self.maps.keys():
            return False

        dir_path = os.path.join(self.get_base_dir(), str(map_id))
        try:
            shutil.rmtree(dir_path)
            self.maps.pop(map_id)
        except OSError as e:
            print("Error in removing map: %s : %s" % (dir_path, e.strerror))
            return False

        return True

    def get_base_dir(self):
        return os.path.join(self.app_config['VIZAR_DATA_DIR'],
                            'incidents',
                            str(self.incident_handler.current_incident),
                            'maps')

    def get_map(self, id):
        if id not in self.maps.keys():
            return None
        return self.maps[id]

    def get_all_maps(self):
        return list(self.maps.values())


def get_map_repository():
    global map_repository
    if map_repository is None:
        map_repository = Repository()

    return map_repository
