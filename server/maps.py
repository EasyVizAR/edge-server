from quart import Blueprint, request

maps = Blueprint('maps', __name__)


'''
Lists all maps found
'''
@maps.route('/maps', methods=['GET'])
async def list_maps():

    # TODO: check authorization

    body = await request.get_json()
    found_maps = []

    # TODO: get list of maps

    return {"code": "200 OK"}

'''
Lists the map with the given id
'''
@maps.route('/maps/<id>', methods=['GET'])
async def show_map(id):

    # TODO: check authorization

    body = await request.get_json()
    found_map = []

    # TODO: get map

    if found_map:
        return {"code": "200 OK",
                "map": found_map}
    else:
        return {"code": "404 NOT FOUND",
                "error": "The requested map does not exist"}

'''
Lists the map features with the given id
'''
@maps.route('/maps/<id>/features', methods=['GET'])
async def list_map_features(id):

    # TODO: check authorization

    body = await request.get_json()
    found_map = []

    # TODO: find map

    if not found_map:
        return {"code": "404 NOT FOUND",
                "error": "The requested map does not exist"}

    # TODO: get map features

'''
Adds a feature to the map with the given id
'''
@maps.route('/maps/<id>/features', methods=['POST'])
async def add_map_feature(id):

    # TODO: check authorization

    body = await request.get_json()
    found_map = []

    # TODO: find map

    if not found_map:
        return {"code": "404 NOT FOUND",
                "error": "The requested map does not exist"}

    # TODO: add features of map
