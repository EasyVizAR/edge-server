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
            map_file = open(maps_path + '/' + str(map_id) + '/map.json')
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
async def show_map(id):
    """
    Lists the map with the given id
    """

    # TODO: check authorization

    try:

        # check if map exists
        found_map_name, maps_path = find_map(id)

        # check if map exists
        if not found_map_name:
            make_response(
                jsonify({"message": "The requested map does not exist", "severity": "Error"}),
                HTTPStatus.NOT_FOUND)

        # get map data
        map_file = open(maps_path + '/' + str(found_map_name) + '/map.json')
        map_data = json.load(map_file)
        map_file.close()

        maps.logger.info('Map ' + str(id) + ' found')

        return make_response(
            jsonify({"map": map_data}),
            HTTPStatus.OK)

    except Exception as e:
        maps.logger.exception('Error getting map ' + str(id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)


@maps.route('/maps/<id>/features', methods=['GET'])
async def list_map_features(id):
    """
    Lists the map features with the given id
    """

    # TODO: check authorization

    try:

        # check if map exists
        found_map_name, maps_path = find_map(id)

        # check if map exists
        if not found_map_name:
            make_response(
                jsonify({"message": "The requested map does not exist", "severity": "Error"}),
                HTTPStatus.NOT_FOUND)

        # get the map features
        map_features_file = open(maps_path + '/' + str(found_map_name) + '/features.json')
        map_features = json.load(map_features_file)
        map_features_file.close()

        maps.logger.info('Map ' + str(id) + ' features found')

        return make_response(
            jsonify({"features": map_features}),
            HTTPStatus.OK)


    except Exception as e:
        maps.logger.exception('Error getting map ' + str(id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)


@maps.route('/maps/<id>/features', methods=['POST'])
async def add_map_feature(id):
    """
    Adds a feature to the map with the given id
    """

    # TODO: check authorization

    body = await request.get_json()
    found_map = []

    try:

        # check if map exists
        found_map_name, maps_path = find_map(id)

        # check if map exists
        if not found_map_name:
            make_response(
                jsonify({"message": "The requested map does not exist", "severity": "Error"}),
                HTTPStatus.NOT_FOUND)

        # get the map features
        map_features_file = open(maps_path + '/' + str(found_map_name) + '/features.json')
        map_features = json.load(map_features_file)
        map_features_file.close()

        # TODO: add features of map
        map_features = None

        return make_response(
            jsonify({"message": "Feature added"}),
            HTTPStatus.CREATED)

    except Exception as e:
        maps.logger.exception('Error getting map ' + str(id) + '.\n' + str(e))

        return make_response(
            jsonify({"message": "Something went wrong", "severity": "Error"}),
            HTTPStatus.INTERNAL_SERVER_ERROR)
