import json
import os
import uuid

import numpy as np
from quart import current_app

from server.utils.utils import GenericJsonEncoder, write_to_file, get_pixels

map_repository = None


class Map:
    def __init__(self, name, image='', intrinsic=None, extrinsic=None, id=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.image = image
        self.extrinsic = extrinsic
        self.intrinsic = intrinsic

    def __str__(self):
        return "id=" + self.id + ", name=" + self.name + ", image=" + str(self.image) + ", extrinsic=" + str(self.extrinsic) + ", intrinsic=" + str(self.intrinsic)


class Feature:
    def __init__(self, name, position, mapId, style, id=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.position = {
            'x': position['x'],
            'y': position['y'],
            'z': position['z']
        }
        self.mapId = mapId
        self.style = {
            "placement": style['placement'],
            "topOffset": style['topOffset'],
            "leftOffset": style['leftOffset'],
            "icon": style['icon']
        }
        self.pixelPosition = {
            "x": None,
            "y": None
        }


class Repository:
    maps = {}
    features = {}

    def __init__(self):
        map_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/')
        os.makedirs(map_dir, exist_ok=True)
        for folder in os.scandir(map_dir):
            if folder.is_dir():
                map = json.load(open(f"{folder.path}/map.json", 'r'))
                intrinsic = None
                extrinsic = None
                image = None
                if 'intrinsic' in map:
                    intrinsic = map['intrinsic']
                if 'extrinsic' in map:
                    extrinsic = map['extrinsic']
                if 'image' in map:
                    image = map['image']
                self.maps[map['id']] = Map(map['name'], image, intrinsic, extrinsic, map['id'])

                features = json.load(open(f"{folder.path}/features.json", 'r'))
                feature_list = []
                if len(features) > 0:
                    for feature in features:
                        print(feature.keys())
                        feature_list.append(Feature(feature['name'], feature['position'], feature['mapId'], feature['style'], id = feature['id']))
                self.features[map['id']] = feature_list

    def create_image(self, intent, data, type, ext = None, ints = None):
        intentId = data['mapID'] if 'maps' == intent else str(uuid.uuid4())
        img_type = type.split("/")[1]
        url = f"{current_app.config['IMAGE_UPLOADS']}{intentId}.{img_type}"
        extrinsic = None
        intrinsic = None
        if ext is not None:
            extrinsic = np.transpose(np.reshape(ext, (4, 4))).tolist()
        if ints is not None:
            intrinsic = np.transpose(np.reshape(ints, (3, 3))).tolist()
        if intent == 'maps' and intrinsic is not None and extrinsic is not None:
            self.maps[intentId].intrinsic = intrinsic
            self.maps[intentId].extrinsic = extrinsic
            filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/',
                                    str(intentId), "map.json")
            write_to_file(json.dumps(self.maps[intentId], cls=GenericJsonEncoder), filepath)

            if intentId in self.features.keys():
                for feature in self.features[intentId]:
                    vector = [feature.position['x'], feature.position['y'], feature.position['z']]
                    pixPos = get_pixels(extrinsic, intrinsic, vector)
                    feature.pixelPosition['x'] = pixPos[0]
                    feature.pixelPosition['y'] = pixPos[1]
                filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/',
                                        str(intentId), "features.json")
                write_to_file(json.dumps(self.features[intentId], cls=GenericJsonEncoder), filepath)

        return {'id': intentId, 'url': url, 'intent': intent, 'data': data, 'type': type, 'intrinsic': intrinsic, 'extrinsic': extrinsic}

    def add_feature(self, id, name, position, mapId, style):
        if mapId not in self.maps.keys():
            return None
        feature = Feature(name, position, mapId, style, id=id)
        if self.maps[mapId].intrinsic is not None and self.maps[mapId].extrinsic is not None:
            vector = [feature.position['x'], feature.position['y'], feature.position['z']]
            pixPos = get_pixels(self.maps[mapId].extrinsic, self.maps[mapId].intrinsic, vector)
            feature.pixelPosition['x'] = pixPos[0]
            feature.pixelPosition['y'] = pixPos[1]

        map_features = []
        if mapId in self.features:
            map_features = self.features[mapId]

        map_features.append(feature)
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/',
                                str(feature.mapId), "features.json")
        write_to_file(json.dumps(map_features, cls=GenericJsonEncoder), filepath)
        self.features[mapId] = map_features
        return feature

    def get_map_features(self, mapId):
        if mapId not in self.features.keys():
            return None
        return self.features[mapId]

    def add_map(self, id, name, image, intrinsic=None, extrinsic=None):
        map = Map(name, image, intrinsic, extrinsic, id)
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/',
                                str(map.id), "map.json")
        write_to_file(json.dumps(map, cls=GenericJsonEncoder), filepath)
        filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'maps/',
                                str(map.id), "features.json")
        write_to_file('[]', filepath)
        self.maps[map.id] = map
        return map.id

    def replace_map(self, id, name, image, intrinsic=None, extrinsic=None):
        if id not in self.maps.keys():
            return None
        id = self.add_map(id, name, image, intrinsic, extrinsic)
        return id

    def get_map(self, id):
        if id not in self.maps.keys():
            return None
        return self.maps[id]

    def get_all_maps(self):
        return self.maps



def get_map_repository():
    global map_repository
    if map_repository is None:
        map_repository = Repository()

    return map_repository
