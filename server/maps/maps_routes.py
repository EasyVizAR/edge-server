import uuid
import os
import json

import pyqrcode

from http import HTTPStatus
from quart import Blueprint, current_app, request, make_response, jsonify, send_from_directory
from werkzeug.utils import secure_filename


maps = Blueprint('maps', __name__)

DEFAULT_ENVIRONMENT_FOLDER = './data'


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

    parent_dir = current_app.config['VIZAR_DATA_DIR']
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
async def list_maps():
    """
    Lists all maps found
    """

    # TODO: check authorization

    all_maps = []

    # open maps directory
    map_list, maps_path = open_maps_dir()

    # add all map data to all_maps
    for map_id in map_list:
        # Ignore the link to the current map because it would result in duplication.
        if map_id == 'current':
            continue

        map_file = open(maps_path + '/' + str(map_id) + '/map.json', 'r')
        map_data = json.load(map_file)
        map_file.close()
        all_maps.append(map_data)

    return await make_response(
        jsonify({"maps": all_maps}),
        HTTPStatus.OK)


@maps.route('/maps/<map_id>', methods=['GET'])
async def show_map(map_id):
    """
    Lists the map with the given id
    """

    # TODO: check authorization

    # check if map exists
    found_map_name, maps_path = find_map(map_id)

    # check if map exists
    if not found_map_name:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # get map data
    map_file = open(maps_path + '/' + str(found_map_name) + '/map.json', 'r')
    map_data = json.load(map_file)
    map_file.close()

    return await make_response(
        jsonify({"map": map_data}),
        HTTPStatus.OK)


@maps.route('/maps/<map_id>/features', methods=['GET'])
async def list_map_features(map_id):
    """
    Lists the map features with the given id
    """

    # TODO: check authorization

    # check if map exists
    found_map_name, maps_path = find_map(map_id)

    # check if map exists
    if not found_map_name:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # get the map features
    map_features_file = open(maps_path + '/' + str(found_map_name) + '/features.json', 'r')
    map_features = json.load(map_features_file)
    map_features_file.close()

    return await make_response(
        jsonify({"features": map_features}),
        HTTPStatus.OK)


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

    if 'new_feature' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)


    # check if map exists
    found_map_name, maps_path = find_map(map_id)

    # check if map exists
    if not found_map_name:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # get new feature
    new_feature = body['new_feature']

    # get the map features
    map_features_file = open(maps_path + '/' + str(found_map_name) + '/features.json', 'r')
    map_features = json.load(map_features_file)
    map_features_file.close()

    # update json
    map_features.update(new_feature)

    # open the file back up to write to it
    map_features_file = open(maps_path + '/' + str(found_map_name) + '/features.json', 'w')

    # write it back to the file
    map_features_file.write(map_features)
    map_features_file.close()

    return await make_response(
        jsonify({"message": "Feature added"}),
        HTTPStatus.CREATED)


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
        path = os.path.join(get_surface_dir(map_id, create=True), filename)
        is_new = not os.path.exists(path)

        with open(path, "wb") as output:
            output.write(body)

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


@maps.route('/maps/<map_id>/replace', methods=['PUT'])
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

    # check if map exists
    found_map_name, maps_path = find_map(map_id)

    # check if map exists
    if not found_map_name:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    map_name = body['name']
    map_image = body['image']

    if not map_name:
        map_name = ''

    if not map_image:
        map_image = ''

    # creates and intializes map json file
    map_file = open(maps_path + '/map.json', 'w')

    map_json_content = {
        'id': map_id,
        'name': map_name,
        'image': map_image
    }

    json_object = json.dumps(map_json_content, indent=4)
    map_file.write(json_object)
    map_file.close()

    # map was created
    return await make_response(
        jsonify({"message": "Map replaced",
                 "map_id": map_id}),
        HTTPStatus.CREATED)


@maps.route('/maps/create', methods=['POST'])
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

    # generate new map id and get map features
    new_id = generate_new_id()
    map_name = body['name']
    map_image = body['image']

    if not map_name:
        map_name = ''

    if not map_image:
        map_image = ''

    if not new_id:
        return await make_response(
            jsonify({"message": "Cannot create map",
                     "severity": "Error"}),
            HTTPStatus.BAD_REQUEST)

    # create the new directory
    map_path = create_map_dir(new_id)

    # check if the directory was created
    if not map_path:
        return await make_response(
            jsonify({"message": "Cannot create map",
                     "severity": "Error"}),
            HTTPStatus.BAD_REQUEST)

    # creates and initializes features file
    features_file = open(map_path + '/features.json', 'w')
    features_file.close()

    # creates and intializes map json file
    map_file = open(map_path + '/map.json', 'w')

    map_json_content = {
        'id': new_id,
        'name': map_name,
        'image': map_image
    }

    json_object = json.dumps(map_json_content, indent=4)
    map_file.write(json_object)
    map_file.close()

    # map was created
    return await make_response(
        jsonify({"message": "Map created",
                 "map_id": new_id}),
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
