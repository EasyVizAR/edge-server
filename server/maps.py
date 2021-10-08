from http import HTTPStatus

from quart import Blueprint, request, make_response, jsonify
import os
import json

maps = Blueprint('maps', __name__)

DEFAULT_ENVIRONMENT_FOLDER = './data'

'''
Lists all maps found
'''
@maps.route('/maps', methods=['GET'])
async def list_maps():

    # TODO: check authorization

    body = await request.get_json()
    found_maps = []

    maps_path = os.environ.get("VIZAR_DATA_DIR", DEFAULT_ENVIRONMENT_FOLDER)
    maps_path += maps_path + '/maps'
    maps_file = os.listdir()

    # TODO: get list of maps

    return {
        'code': '200 OK',
        'maps': found_maps
    }

'''
Lists the map with the given id
'''
@maps.route('/maps/<id>', methods=['GET'])
async def show_map(id):

    # TODO: check authorization

    body = await request.get_json()
    found_map = []

    # TODO: get map
    try:
        if found_map:
            return (found_map, 200)
        else:
            return ({"error": "The requested map does not exist"}, 404)
    except Exception as e:
        return ({"error": e}, 500)

'''
Lists the map features with the given id
'''
@maps.route('/maps/<id>/features', methods=['GET'])
async def list_map_features(id):

    maps.logger.info('getting map ' + str(id))

    # TODO: check authorization

    try:
        found_map_name = None

        maps_path = os.environ.get("VIZAR_DATA_DIR", DEFAULT_ENVIRONMENT_FOLDER)
        maps_path += maps_path + '/maps'
        maps_list = os.listdir(maps_path)

        # find map given the id
        for map in maps_list:
            if id == map:
                found_map_name = map
                break

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


'''
Adds a feature to the map with the given id
'''
@maps.route('/maps/<id>/features', methods=['POST'])
async def add_map_feature(id):

    # TODO: check authorization

    body = await request.get_json()
    found_map = []

    try:
        found_map_name = None

        maps_path = os.environ.get("VIZAR_DATA_DIR", DEFAULT_ENVIRONMENT_FOLDER)
        maps_path += maps_path + '/maps'
        maps_list = os.listdir(maps_path)

        # find map given the id
        for map in maps_list:
            if id == map:
                found_map_name = map
                break

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
