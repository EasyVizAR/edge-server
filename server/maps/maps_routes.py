from http import HTTPStatus
from quart import Blueprint, request, make_response, jsonify
import os
import json

maps = Blueprint('maps', __name__)

DEFAULT_ENVIRONMENT_FOLDER = './data'


def open_maps_dir():
    """
    Opens the maps directory
    """

    maps_path = os.environ.get("VIZAR_DATA_DIR", DEFAULT_ENVIRONMENT_FOLDER)
    maps_path += maps_path + '/maps'
    maps_list = os.listdir(maps_path)

    return maps_list, maps_path


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

    parent_dir = os.environ.get("VIZAR_DATA_DIR", DEFAULT_ENVIRONMENT_FOLDER)
    path = os.path.join(parent_dir, map_id)

    try:
        os.mkdir(path)
    except Exception as e:
        return None

    return path


@maps.route('/maps', methods=['GET'])
async def list_maps():
    """
    Lists all maps found
    """

    # TODO: check authorization

    try:
        all_maps = []

        # open maps directory
        maps_list, maps_path = open_maps_dir()

        # add all map data to all_maps
        for map_id in maps_list:
            map_file = open(maps_path + '/' + str(map_id) + '/map.json', 'r')
            map_data = json.load(map_file)
            map_file.close()
            all_maps.append(map_data)

        return make_response(
            jsonify({"maps": all_maps}),
            HTTPStatus.OK)

    except Exception as e:
        maps.logger.exception('Error getting map ' + str(id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)


@maps.route('/maps/<id>', methods=['GET'])
async def show_map(map_id):
    """
    Lists the map with the given id
    """

    # TODO: check authorization

    try:

        # check if map exists
        found_map_name, maps_path = find_map(map_id)

        # check if map exists
        if not found_map_name:
            make_response(
                jsonify({"message": "The requested map does not exist", "severity": "Error"}),
                HTTPStatus.NOT_FOUND)

        # get map data
        map_file = open(maps_path + '/' + str(found_map_name) + '/map.json', 'r')
        map_data = json.load(map_file)
        map_file.close()

        maps.logger.info('Map ' + str(map_id) + ' found')

        return make_response(
            jsonify({"map": map_data}),
            HTTPStatus.OK)

    except Exception as e:
        maps.logger.exception('Error getting map ' + str(map_id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)


@maps.route('/maps/<id>/features', methods=['GET'])
async def list_map_features(map_id):
    """
    Lists the map features with the given id
    """

    # TODO: check authorization

    try:

        # check if map exists
        found_map_name, maps_path = find_map(map_id)

        # check if map exists
        if not found_map_name:
            make_response(
                jsonify({"message": "The requested map does not exist", "severity": "Error"}),
                HTTPStatus.NOT_FOUND)

        # get the map features
        map_features_file = open(maps_path + '/' + str(found_map_name) + '/features.json', 'r')
        map_features = json.load(map_features_file)
        map_features_file.close()

        maps.logger.info('Map ' + str(map_id) + ' features found')

        return make_response(
            jsonify({"features": map_features}),
            HTTPStatus.OK)


    except Exception as e:
        maps.logger.exception('Error getting map ' + str(map_id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)


@maps.route('/maps/<id>/features', methods=['POST'])
async def add_map_feature(map_id):
    """
    Adds a feature to the map with the given id
    """

    # TODO: check authorization

    body = await request.get_json()

    try:

        # check if map exists
        found_map_name, maps_path = find_map(map_id)

        # check if map exists
        if not found_map_name:
            make_response(
                jsonify({"  message": "The requested map does not exist", "severity": "Error"}),
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

        return make_response(
            jsonify({"message": "Feature added"}),
            HTTPStatus.CREATED)

    except Exception as e:
        maps.logger.exception('Error getting map ' + str(map_id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)


@maps.route('/maps/create', methods=['POST'])
def create_map():
    """
    Creates a map
    """

    # TODO check authorization

    body = await request.get_json()

    # generate new map id and get map features
    new_id = None
    map_name = body.get('name')
    map_image = body.get('image')

    if not map_name:
        map_name = ''

    if not map_image:
        map_image = ''

    # create the new directory
    map_path = create_map_dir(new_id)

    # check if the directory was created
    if not map_path:
        return make_response(jsonify({"message": "Cannot create map", "severity": "Error"}),
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
    return make_response(jsonify({"message": "Map created", "map_id": new_id}),
                         HTTPStatus.CREATED)
