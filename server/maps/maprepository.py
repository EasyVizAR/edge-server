import json
import os
import uuid
import shutil

import numpy as np
from quart import current_app, g

from server.utils.utils import GenericJsonEncoder, write_to_file, get_pixels, get_vector

map_repository = None


class Map:
    def __init__(self, name, image='', incident=-1, id=None, viewBox=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name

        # set default image if there is not a url
        if image is None or image == '':
            self.image = '/maps/' + str(self.id) + '/floor-plan.svg'
        else:
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
    def __init__(self, name, ftype, mapId, style, id=None, position=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.type = ftype
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
            "radius": 10 if style.get('radius') is None else style.get('radius')
            # TODO: change default value 10 to exception later
        }


class Repository:
    maps = {}
    features = {}

    def __init__(self, app=current_app):
        self.app_config = app.config

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
                        feature_obj = Feature(feature['name'], feature['type'], feature['mapId'], feature['style'],
                                              id=feature['id'], position=feature['position'])
                        feature_list.append(feature_obj)
                self.features[map['id']] = feature_list

    def create_image(self, intent, data, type, viewBox=None):
        intentId = data['mapID'] if 'maps' == intent else str(uuid.uuid4())
        img_type = "svg" if type.split("/")[1] == "svg+xml" else type.split("/")[1]
        url = f"{current_app.config['IMAGE_UPLOADS']}{intentId}.{img_type}"
        if intent == 'maps' and viewBox is not None:
            self.maps[intentId].viewBox = viewBox
            filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'],
                                    f"incidents/{g.active_incident.id}/maps/",
                                    str(intentId), "map.json")
            write_to_file(json.dumps(self.maps[intentId], cls=GenericJsonEncoder), filepath)

        return {'id': intentId, 'url': url, 'intent': intent, 'data': data, 'type': type, 'viewBox': viewBox}

    def add_feature(self, id, name, ftype, mapId, style, position=None):
        if mapId not in self.maps.keys():
            return None

        feature = Feature(name, ftype, mapId, style, id=id)

        # add position if the placement of the feature is point
        if style.get('placement') == 'point' or style.get('placement') == 'floating':
            feature.position['x'] = position['x']
            feature.position['y'] = position['y']
            feature.position['z'] = position['z']

        if style.get('placement') == 'floating':
            feature.style['radius'] = 10 if style.get('radius') is None else style.get('radius')

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

    def add_map(self, id, name, image, dummyData=False, viewBox=None):
        map = Map(name, image, incident=g.active_incident.id, id=id, viewBox=viewBox)
        if dummyData:
            image = '/uploads/' + map.id + '.svg'
            map.image = image
        filepath = os.path.join(self.get_base_dir(), str(map.id), "map.json")
        write_to_file(json.dumps(map, cls=GenericJsonEncoder), filepath)
        filepath = os.path.join(self.get_base_dir(), str(map.id), "features.json")
        write_to_file('[]', filepath)
        self.maps[map.id] = map
        if dummyData:
            self.create_dummy_data(map)
        return map.id

    def create_dummy_data(self, map):
        from server.headset.headsetrepository import get_headset_repository
        import urllib.request
        URL = 'https://pages.cs.wisc.edu/~hartung/easyvizar/seventhfloor.svg'
        headsetRepo = get_headset_repository()

        self.create_image("maps", data={"mapID": map.id}, type="image/svg+xml",
                             viewBox=[-35.44230853629791, -1.7768587228105028, 39.10819374001562, 52.83971533602437])
        urllib.request.urlretrieve(URL, f'server/frontend/build{map.image}')

        self.add_feature(None, "Fire-1", "fire", map.id, style={
            "leftOffset": "0",
            "placement": "point",
            "topOffset": "0"
        }, position={
            "x": -18.155353332377956,
            "y": 0,
            "z": 24.84940408323303
        })
        self.add_feature(None, "Fire-2", "fire", map.id, style={
            "leftOffset": "0",
            "placement": "point",
            "topOffset": "0"
        }, position={
            "x": -20.121572844333024,
            "y": 0,
            "z": 22.0459319977115
        })
        self.add_feature(None, "Fire-3", "fire", map.id, style={
            "leftOffset": "0",
            "placement": "floating",
            "topOffset": "0",
            "radius": "2"
        }, position={
            "x": -27.655278809303645,
            "y": 0,
            "z": 43.13419236018029
        })
        self.add_feature(None, "Fire-4", "fire", map.id, style={
            "leftOffset": "0",
            "placement": "floating",
            "topOffset": "0",
            "radius": "3"
        }, position={
            "x": -31.806898977366878,
            "y": 0,
            "z": 4.342902801868337
        })

        headsetRepo.add_headset("Headset-1", position={
            "x": -5,
            "y": 0,
            "z": 5
        }, mapId="cs-2", id=None)
        headsetRepo.add_headset("Headset-2", position={
            "x": -3,
            "y": 0,
            "z": 1
        }, mapId="cs-2", id=None)


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
                            g.active_incident.id,
                            'maps')

    def get_map(self, id):
        if id not in self.maps.keys():
            return None
        return self.maps[id]

    def get_all_maps(self):
        return list(self.maps.values())

    def get_map_filepath(self, map_id):

        # check if map exists
        if map_id not in self.maps.keys():
            return None

        # get current incident number
        current_incident = g.active_incident.id

        # create path and return
        return os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents', str(current_incident), 'maps', map_id)

    def reset_maps_for_new_incident(self):
        self.maps = {}

    def reset_maps_for_previous_incident(self, incident):
        self.maps = {}
        base_filepath = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'incidents', str(incident), 'maps')

        for folder in os.scandir(base_filepath):
            if folder.is_dir():
                map_info_filepath = os.path.join(base_filepath, folder.name, 'map.json')
                try:
                    info = open(map_info_filepath)
                    data = json.load(info)
                    info.close()

                    if data.get('id'):
                        new_map = Map(data.get('name'), image=data.get('image'), incident=data.get('incident'),
                                      id=data.get('id'), viewBox=data.get('viewBox'))
                        self.maps[data.get('id')] = new_map

                except FileNotFoundError as e:
                    # At least for now, it should not be a problem if the file does not exist.
                    return False
        return True


def get_map_repository():
    global map_repository
    if map_repository is None:
        map_repository = Repository()

    return map_repository
