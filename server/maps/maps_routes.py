import asyncio
import functools
import json
import os
import uuid

import pyqrcode

from http import HTTPStatus
from quart import Blueprint, current_app, request, make_response, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from server.mapping.floorplanner import Floorplanner
from server.maps.mapping_thread import MappingThread
from server.maps.maprepository import get_map_repository
from server.utils.utils import get_pixels, GenericJsonEncoder

maps = Blueprint('maps', __name__)

mapping_threads = dict()


def initialize_maps(app):
    """
    Initialize maps storage.

    Make sure the maps directory exists, and create a new "current" map if one
    does not exist. This may make starting up a new system easier.
    """
    data_dir = app.config['VIZAR_DATA_DIR']
    maps_dir = os.path.join(data_dir, 'maps')
    os.makedirs(maps_dir, exist_ok=True)

    if not os.path.exists(os.path.join(maps_dir, 'current')):
        map_id = str(generate_new_id())

        # Create surfaces subdirectory.
        subdir = os.path.join(maps_dir, map_id)
        os.makedirs(os.path.join(subdir, 'surfaces'))

        # Initialize features file
        features_file = open(os.path.join(subdir, 'features.json'), 'w')
        features_file.close()

        map_info = {
            'id': map_id,
            'name': 'New Map'
        }

        # Initialize map file
        map_file = open(os.path.join(subdir, 'map.json'), 'w')
        map_file.write(json.dumps(map_info))
        map_file.close()

        os.symlink(map_id, os.path.join(maps_dir, 'current'), target_is_directory=True)


def open_maps_dir():
    """
    Opens the maps directory
    """
    data_dir = current_app.config['VIZAR_DATA_DIR']
    maps_path = os.path.join(data_dir, "maps")
    os.makedirs(maps_path, exist_ok=True)
    maps_list = os.listdir(maps_path)
    return maps_list, maps_path


def get_surface_dir(map_id, create=True):
    """
    Returns the directory for map surfaces.
    """
    data_dir = current_app.config['VIZAR_DATA_DIR']
    surface_dir = os.path.join(data_dir, "maps", map_id, "surfaces")
    if create:
        os.makedirs(surface_dir, exist_ok=True)
    return surface_dir


def find_map(map_id):
    """
    Finds the map related to the given id
    """

    # opens maps directory
    maps_list, maps_path = open_maps_dir()

    # find map given the id
    for map_dir in maps_list:
        if map_id == map_dir:
            return map_dir, maps_path
            break

    # map not found
    return None, None


def create_map_dir(map_id):
    """
    creates new map directory

    :param map_id:
    :return None if the directory cannot be created, else return the path:
    """
    if not map_id:
        return None

    parent_dir = current_app.config['VIZAR_DATA_DIR'] + 'maps/'
    path = os.path.join(parent_dir, map_id)

    try:
        os.mkdir(path)
    except Exception as e:
        return None

    return path


def generate_new_id():
    """
    Creates new map id
    :return: map id
    """

    return uuid.uuid1()


@maps.route('/maps', methods=['GET'])
async def get_all_maps():
    """
    Lists all maps found
    """

    # TODO: check authorization
    maps = get_map_repository().get_all_maps()
    return jsonify(maps), HTTPStatus.OK


@maps.route('/maps/<map_id>', methods=['GET'])
async def show_map(map_id):
    """
    Lists the map with the given id
    """

    # TODO: check authorization

    # check if map exists
    found_map_name, maps_path = find_map(map_id)
    map = get_map_repository().get_map(map_id)
    print(map)
    # check if map exists
    if map is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)
    else:
        return jsonify(map), HTTPStatus.OK


@maps.route('/maps/<map_id>/features', methods=['GET'])
async def list_map_features(map_id):
    """
    Lists the map features with the given id
    """

    # TODO: check authorization

    features = get_map_repository().get_map_features(map_id)

    # check if map exists
    if features is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)
    else:
        return jsonify(features), HTTPStatus.OK


@maps.route('/maps/<map_id>/features', methods=['POST'])
async def add_map_feature(map_id):
    """
    Adds a feature to the map with the given id
    """

    # TODO: check authorization

    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body or 'mapID' not in body\
            or ('position' not in body and 'pixelPosition' not in body) or 'style' not in body:
        return await make_response(jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
                                   HTTPStatus.BAD_REQUEST)

    if 'pixelPosition' in body:
        feature = get_map_repository().add_feature(body['id'],
                                                   body['name'],
                                                   body['mapID'],
                                                   body['style'],
                                                   pixelPosition=body['pixelPosition'])
    else:
        feature = get_map_repository().add_feature(body['id'],
                                                   body['name'],
                                                   body['mapID'],
                                                   body['style'],
                                                   position=body['position'])

    # check if map exists
    if feature is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    else:
        return jsonify(feature), HTTPStatus.CREATED


@maps.route('/maps/<map_id>/surfaces', methods=['GET'])
async def list_map_surfaces(map_id):
    """
    Get list of surfaces associated with a map.
    ---
    get:
        description: List surfaces
        responses:
            200:
                description: A list of surfaces.
                content:
                    application/json:
                        schema:
                            type: array
                            items: SurfaceFileInformationSchema
    """

    # TODO check authorization

    surface_dir = get_surface_dir(map_id, create=False)

    surfaces = []
    for entry in os.scandir(surface_dir):
        if not entry.name.startswith('.') and entry.is_file():
            stat = entry.stat()
            surfaces.append({
                "id": os.path.splitext(entry.name)[0],
                "filename": entry.name,
                "modified": stat.st_mtime,
                "size": stat.st_size
            })

    return jsonify(surfaces), HTTPStatus.OK


@maps.route('/maps/<map_id>/surfaces/<surface_id>', methods=['PUT'])
async def replace_surface(map_id, surface_id):
    """
    Replace a surface.

    This expects to receive a PLY file and stores it in the data directory.
    ---
    put:
        description: Create or update a surface
        responses:
            200:
                description: A surface file information object
                content:
                    application/json:
                        schema: SurfaceFileInformationSchema
    """

    # TODO check authorization

    body = await request.get_data()
    if body[0:3].decode() == "ply":
        filename = secure_filename("{}.ply".format(surface_id))
        surface_dir = get_surface_dir(map_id, create=True)
        path = os.path.join(surface_dir, filename)
        is_new = not os.path.exists(path)

        with open(path, "wb") as output:
            output.write(body)

        if map_id not in mapping_threads:
            data_dir = current_app.config['VIZAR_DATA_DIR']
            map_dir = os.path.join(data_dir, 'maps', map_id)
            mapping_threads[map_id] = MappingThread(map_dir)
            mapping_threads[map_id].start()

        mapping_threads[map_id].notify()

        stat = os.stat(path)
        surface = {
            "id": surface_id,
            "filename": filename,
            "modified": stat.st_mtime,
            "size": stat.st_size
        }

        if is_new:
            return surface, HTTPStatus.CREATED
        else:
            return surface, HTTPStatus.OK


@maps.route('/maps/<map_id>/', methods=['PUT'])
async def replace_map(map_id):
    """
    Replaces a current map
    :return: 201 if the map was replaced
    """

    # TODO check authorization

    if not map_id:
        return await make_response(
            jsonify({"message": "No map id",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    # get body of request
    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body or 'image' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    map_name = body['name']
    map_image = body['image']

    id = get_map_repository().replace_map(map_id, map_name, map_image)

    # check if map exists
    if id is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # map was created
    return await make_response(
        jsonify({"message": "Map replaced",
                 "map_id": id}),
        HTTPStatus.CREATED)


@maps.route('/maps/<map_id>', methods=['DELETE'])
async def delete_map(map_id):

    # TODO check authorization

    if not map_id:
        return await make_response(jsonify({"message": "No map id", "severity": "Warning"}), HTTPStatus.BAD_REQUEST)

    deleted = get_map_repository().remove_map(map_id)

    if deleted:

        # map was deleted
        return await make_response(jsonify({"message": "Map deleted"}), HTTPStatus.OK)
    else:

        # map was deleted
        return await make_response(jsonify({"message": "Map could not be deleted"}), HTTPStatus.BAD_REQUEST)


@maps.route('/maps', methods=['POST'])
async def create_map():
    """
    Creates a map
    """

    # TODO check authorization

    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body or 'image' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    id = None
    if 'id' in body and str(body['id']).strip() != '':
        id = body['id']

    created_id = get_map_repository().add_map(id, body['name'], body['image'])

    return await make_response(
        jsonify({"message": "Map created",
                 "map_id": created_id}),
        HTTPStatus.CREATED)


@maps.route('/image-uploads/', methods=['POST'])
async def image_upload():
    """
    Initiate a file upload
    ---
    post:
        description: Initiate a file upload
        responses:
            200:
                description: A file upload object
                content:
                    application/json:
                        schema: ImageUploadSchema
    """
    body = await request.get_json()

    if 'intent' not in body or 'data' not in body or 'type' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)
    elif 'maps' == body['intent'] and 'mapID' not in body['data']: # TODO: What is the condition for -> For a feature, it should include bounding box(es) and feature labels.?
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    return await make_response(jsonify(get_map_repository().create_image(body['intent'], body['data'], body['type'], body['extrinsic'], body['intrinsic'])),
                               HTTPStatus.CREATED)


@maps.route('/maps/<map_id>/qrcode', methods=['GET'])
async def get_map_qrcode(map_id):
    """
    Get a QR code for the map.
    ---
    get:
        description: List surfaces
        responses:
            200:
                description: A list of surfaces.
                content: image/svg+xml
    """

    # TODO check authorization

    data_dir = current_app.config['VIZAR_DATA_DIR']
    map_dir = os.path.join(data_dir, 'maps', map_id)
    image_path = os.path.join(map_dir, 'qrcode.svg')

    if not os.path.isdir(map_dir):
        return {"error": "Map does not exist."}, HTTPStatus.NOT_FOUND

    if not os.path.exists(image_path):
        url = 'vizar://{}/maps/{}'.format(current_app.config['VIZAR_EDGE_HOST'], map_id)

        code = pyqrcode.create(url, error='L')
        code.svg(image_path, title=url)

    return await send_from_directory(map_dir, 'qrcode.svg')


@maps.route('/maps/<map_id>/top-down.svg', methods=['GET'])
async def get_map_topdown(map_id):
    data_dir = current_app.config['VIZAR_DATA_DIR']
    map_dir = os.path.join(data_dir, 'maps', map_id)
    image_path = os.path.join(map_dir, 'top-down.svg')

    # This should be the common case. The mapping thread runs in the
    # background and produces up-to-date images.
    if os.path.exists(image_path):
        return await send_from_directory(map_dir, 'top-down.svg')

    # If the image happens to not exist for some reason, we can do a one-time
    # calculation. This will be a bit slow, unfortunately.
    def create_map():
        ply_files = os.path.join(map_dir, 'surfaces', '*.ply')
        json_file = os.path.join(map_dir, 'top-down.json')
        floorplanner = Floorplanner(ply_files, json_file)
        floorplanner.update_lines(initialize=False)
        floorplanner.write_image(image_path)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, create_map)

    return await send_from_directory(map_dir, 'top-down.svg')
