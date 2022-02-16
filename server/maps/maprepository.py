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
    def __init__(self, name, image='', intrinsic=None, extrinsic=None, id=None, incident=-1, viewBox=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.image = image
        self.extrinsic = extrinsic
        self.intrinsic = intrinsic
        self.incident = incident

        if viewBox is None:
            self.viewBox = dict(left=0, top=0, width=0, height=0)
        else:
            self.viewBox = viewBox

    def __str__(self):
        return "id=" + self.id + ", name=" + self.name + ", image=" + str(self.image) + ", extrinsic=" + str(
            self.extrinsic) + ", intrinsic=" + str(self.intrinsic)

    def save(self):
        path = os.path.join(get_map_repository().get_base_dir(), self.id, "map.json")
        with open(path, "w") as output:
            output.write(json.dumps(self, cls=GenericJsonEncoder))


class Feature:
    def __init__(self, name, mapId, style, id=None, position=None, pixelPosition=None):
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
        self.style = style
        if pixelPosition is not None:
            self.pixelPosition = {
                "x": pixelPosition['x'],
                "y": pixelPosition['y']
            }
        else:
            self.pixelPosition = {
                "x": None,
                "y": None
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
                intrinsic = map.get('intrinsic')
                extrinsic = map.get('extrinsic')
                image = map.get('image')
                viewBox = map.get('viewBox')
                self.maps[map['id']] = Map(map['name'], image, intrinsic, extrinsic, map['id'],
                                           viewBox=viewBox,
                                           incident=self.incident_handler.current_incident)

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
                        if 'pixelPosition' in feature:
                            if 'x' in feature['pixelPosition']:
                                feature_obj.pixelPosition['x'] = feature['pixelPosition']['x']
                            if 'y' in feature['pixelPosition']:
                                feature_obj.pixelPosition['y'] = feature['pixelPosition']['y']
                        feature_list.append(feature_obj)
                self.features[map['id']] = feature_list

    def create_image(self, intent, data, type, ext=None, ints=None):
        intentId = data['mapID'] if 'maps' == intent else str(uuid.uuid4())
        img_type = type.split("/")[1]
        url = f"{self.app_config['IMAGE_UPLOADS']}{intentId}.{img_type}"
        extrinsic = None
        intrinsic = None
        if ext is not None:
            extrinsic = np.transpose(np.reshape(ext, (4, 4))).tolist()
        if ints is not None:
            intrinsic = np.transpose(np.reshape(ints, (3, 3))).tolist()
        if intent == 'maps' and intrinsic is not None and extrinsic is not None:
            self.maps[intentId].intrinsic = intrinsic
            self.maps[intentId].extrinsic = extrinsic
            filepath = os.path.join(self.get_base_dir(), str(intentId), "map.json")
            write_to_file(json.dumps(self.maps[intentId], cls=GenericJsonEncoder), filepath)

            if intentId in self.features.keys():
                for feature in self.features[intentId]:
                    vector = [feature.position['x'], feature.position['y'], feature.position['z']]
                    pixPos = get_pixels(extrinsic, intrinsic, vector)
                    feature.pixelPosition['x'] = pixPos[0]
                    feature.pixelPosition['y'] = pixPos[1]
                filepath = os.path.join(self.get_base_dir(), str(intentId), "features.json")
                write_to_file(json.dumps(self.features[intentId], cls=GenericJsonEncoder), filepath)

        return {'id': intentId, 'url': url, 'intent': intent, 'data': data, 'type': type, 'intrinsic': intrinsic,
                'extrinsic': extrinsic}

    def add_feature(self, id, name, mapId, style, position=None, pixelPosition=None):
        if mapId not in self.maps.keys():
            return None

        feature = Feature(name, mapId, style, id=id)
        if self.maps[mapId].intrinsic is not None and self.maps[mapId].extrinsic is not None:
            if position is not None:
                vector = [feature.position['x'], feature.position['y'], feature.position['z']]
                pixPos = get_pixels(self.maps[mapId].extrinsic, self.maps[mapId].intrinsic, vector)
                feature.pixelPosition['x'] = pixPos[0]
                feature.pixelPosition['y'] = pixPos[1]
            else:
                pixPos = [pixelPosition['x'], pixelPosition['y']]
                vector = get_vector(self.maps[mapId].extrinsic, self.maps[mapId].intrinsic, pixPos)
                feature.position['x'] = vector[0]
                feature.position['y'] = vector[1]
                feature.position['z'] = vector[2]

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

    def add_map(self, id, name, image, intrinsic=None, extrinsic=None, viewBox=None):
        map = Map(name, image, intrinsic, extrinsic, id, incident=self.incident_handler.current_incident, viewBox=viewBox)
        filepath = os.path.join(self.get_base_dir(), str(map.id), "map.json")
        write_to_file(json.dumps(map, cls=GenericJsonEncoder), filepath)
        filepath = os.path.join(self.get_base_dir(), str(map.id), "features.json")
        write_to_file('[]', filepath)
        self.maps[map.id] = map
        return map.id

    def replace_map(self, id, name, image, intrinsic=None, extrinsic=None):
        if id not in self.maps.keys():
            return None

        id = self.add_map(id, name, image, intrinsic, extrinsic, incident=self.incident_handler.current_incident)
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
