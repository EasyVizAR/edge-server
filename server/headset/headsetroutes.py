import json
import os
from http import HTTPStatus

from quart import request, jsonify, make_response, Blueprint, current_app, send_file
from werkzeug.utils import secure_filename

from server.headset.headsetrepository import get_headset_repository
from server.utils.utils import GenericJsonEncoder, save_image

blueprint = Blueprint('headsets', __name__)


@blueprint.route('/headsets', methods=['GET'])
async def get_all():
    """
    List headsets
    ---
    get:
        description: List headsets
        responses:
            200:
                description: A list of headsets.
                content:
                    application/json:
                        schema:
                            type: array
                            items: HeadsetSchema
    """
    headsets = get_headset_repository().get_all_headsets()
    return jsonify(headsets), HTTPStatus.OK


@blueprint.route('/headsets/<id>', methods=['GET'])
async def get(id):
    """
    Get headset
    ---
    get:
        description: Get a headset
        responses:
            200:
                description: A headset
                content:
                    application/json:
                        schema: HeadsetSchema
    """
    headset = get_headset_repository().get_headset(id)

    if headset is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)
    else:
        return jsonify(headset), HTTPStatus.OK


@blueprint.route('/headsets', methods=['POST'])
async def register():
    """
    Register a headset
    ---
    post:
        description: Register a headset
        responses:
            200:
                description: A headset
                content:
                    application/json:
                        schema: HeadsetSchema
    """
    body = await request.get_json()

    if 'name' not in body:
        return await make_response(jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
                                   HTTPStatus.BAD_REQUEST)

    # TODO: Finalize authentication method

    headset = {
        'name': body['name'],
        'mapId': body.get('mapId', 'current'),
        'position': body.get('position')
    }

    headset['id'] = get_headset_repository().add_headset(headset['name'], headset['position'], headset['mapId'])

    return jsonify(headset), HTTPStatus.OK


@blueprint.route('/headsets/authenticate/', methods=['POST'])
async def authenticate():
    """
    Authenticate a headset
    ---
    post:
        description: Authenticate a headset
        responses:
            200:
                description: Authentication response
    """
    body = await request.get_json()

    if 'password' not in body or 'username' not in body:
        return await make_response(jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
                                   HTTPStatus.BAD_REQUEST)

    username = body['username']
    password = body['password']

    # TODO: Generate token or session
    token = username + password

    return await make_response({"token": token}, HTTPStatus.OK)


@blueprint.route('/headsets/<headsetId>/updates', methods=['GET'])
async def get_updates(headsetId):
    """
    Get headset updates
    """

    headset = get_headset_repository().get_headset(headsetId)
    if headset is None:
        return {"message": "The requested headset does not exist."}, HTTPStatus.NOT_FOUND

    updates = headset.get_updates()
    return jsonify(updates)


@blueprint.route('/headsets/<headsetId>/updates', methods=['POST'])
async def update_position(headsetId):
    """
    Update a headset
    ---
    post:
        description: Create a new headset update
        parameters:
            - in: body
              required: true
              schema: HeadsetUpdateSchema
        responses:
            200:
                description: A headset update object
                content:
                    application/json:
                        schema: HeadsetUpdateSchema
    """
    body = await request.get_json()

    if 'position' not in body or 'orientation' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    position = body['position']
    orientation = body['orientation']

    headset_update = get_headset_repository().update_pose(headsetId, position, orientation)

    if headset_update is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)

    else:
        return jsonify(headset_update), HTTPStatus.OK


@blueprint.route('/image-upload/<imageId>', methods=['POST'])
async def upload(imageId):
    request_files = await request.files
    image = request_files['image']
    folder_path = current_app.config['VIZAR_DATA_DIR'] + current_app.config['IMAGE_UPLOADS']
    file_path = os.path.join(folder_path, str(secure_filename(image.filename)))
    await save_image(file_path, image)
    return await make_response({'success': 'true'})


@blueprint.route('/headsets/<headsetId>/', methods=['PUT'])
async def update_headset(headsetId):

    if not headsetId:
        return await make_response(
            jsonify({"message": "No headset id",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    # get body of request
    body = await request.get_json()

    # check if the request has all the required information
    if 'name' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    # update the info in the repo
    returned_id = get_headset_repository().update_headset_name(headsetId, body['name'])

    # check if headset exists
    if returned_id is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # headset was updated
    return await make_response(
            jsonify({"message": "Headset updated",
                     "headset_id": returned_id}),
            HTTPStatus.CREATED)

# @blueprint.route('/map-image/<mapId>', methods=['GET'])
# async def get_image(mapId):
#     folder_path = current_app.config['VIZAR_DATA_DIR'] + current_app.config['IMAGE_UPLOADS']
#     file_path = os.path.join(folder_path, f"{mapId}.jpeg")
#     print(f"Sending file {file_path}")
#     return await send_file(file_path, as_attachment=True)

