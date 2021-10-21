import json
from http import HTTPStatus

from quart import request, jsonify, make_response, Blueprint

from server.headset.headsetrepository import get_headset_repository
from server.utils.utils import GenericJsonEncoder

blueprint = Blueprint('headsets', __name__)


@blueprint.route('/headsets', methods=['GET'])
async def get_all():
    headsets = get_headset_repository().headsets
    return await make_response(jsonify(headsets), HTTPStatus.OK)


@blueprint.route('/headsets/<id>', methods=['GET'])
async def get(id):
    headset = get_headset_repository().get_headset(id)

    if headset is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)

    return await make_response(jsonify(json.dumps(headset, cls=GenericJsonEncoder)), HTTPStatus.OK)


@blueprint.route('/headsets/register/', methods=['POST'])
async def register():
    body = await request.get_json()

    if 'name' not in body or 'position' not in body or 'mapId' not in body:
        return await make_response(jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
                                   HTTPStatus.BAD_REQUEST)

    # TODO: Finalize authentication method
    name = body['name']
    position = body['position']
    mapId = body['mapId']
    headset_id = get_headset_repository().add_headset(name, position, mapId)

    return await make_response({'id': headset_id}, HTTPStatus.OK)


@blueprint.route('/headsets/authenticate/', methods=['POST'])
async def authenticate():
    body = await request.get_json()

    if 'password' not in body or 'username' not in body:
        return await make_response(jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
                                   HTTPStatus.BAD_REQUEST)

    username = body['username']
    password = body['password']

    # TODO: Generate token or session
    token = username + password

    return await make_response({"token": token}, HTTPStatus.OK)


@blueprint.route('/headsets/<headsetId>/updates/', methods=['POST'])
async def update_position(headsetId):
    body = await request.get_json()

    if 'x' not in body or 'y' not in body or 'z' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    position = {'x': body['x'], 'y': body['y'], 'z': body['z']}
    updated_headset = get_headset_repository().update_position(headsetId, position)

    if updated_headset is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)

    return await make_response(jsonify(json.dumps(updated_headset, cls=GenericJsonEncoder)), HTTPStatus.OK)


# TODO: will this be in a separate file?
@blueprint.route('/image-uploads/', methods=['POST'])
async def image_upload():
    body = await request.get_json()

    if 'intent' not in body or 'data' not in body or 'type' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)
    elif 'maps' == body['intent'] and 'mapID' not in body['data']: # TODO: What is the condition for -> For a feature, it should include bounding box(es) and feature labels.?
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    return await make_response(jsonify(get_headset_repository().create_image(body['intent'], body['data'], body['type'])),
                               HTTPStatus.CREATED)
