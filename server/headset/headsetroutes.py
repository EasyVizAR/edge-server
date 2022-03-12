import asyncio
import json
import os

from http import HTTPStatus

from quart import request, jsonify, make_response, Blueprint, current_app, send_file
from werkzeug.utils import secure_filename

from server.headset.headsetrepository import get_headset_repository
from server.incidents.incident_handler import init_incidents_handler
from server.utils.utils import GenericJsonEncoder, save_image

blueprint = Blueprint('headsets', __name__)


@blueprint.route('/headsets', methods=['GET'])
async def get_all():
    """
    List headsets
    ---
    get:
        description: List headsets
        tags:
          - headsets
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of headsets.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Headset
    """
    headsets = get_headset_repository().get_all_headsets()

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): headsets}
    else:
        result = headsets

    return jsonify(result), HTTPStatus.OK


@blueprint.route('/headsets/<id>', methods=['GET'])
async def get(id):
    """
    Get headset
    ---
    get:
        description: Get a headset
        tags:
          - headsets
        parameters:
          - name: id
            in: path
            required: true
            description: Headset ID
        responses:
            200:
                description: A headset
                content:
                    application/json:
                        schema: Headset
    """
    headset = get_headset_repository().get_headset(id)

    if headset is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)
    else:
        return jsonify(headset), HTTPStatus.OK


@blueprint.route('/headsets/<headset_id>/poses', methods=['POST'])
async def create_headset_pose(headset_id):
    """
    Create headset pose
    ---
    post:
        description: Create a new headset pose
        tags:
          - headsets
        requestBody:
            required: true
            content:
                application/json:
                    schema: HeadsetPose
        responses:
            200:
                description: A headset pose object
                content:
                    application/json:
                        schema: HeadsetUpdate
    """
    body = await request.get_json()

    if 'position' not in body or 'orientation' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    position = body['position']
    orientation = body['orientation']

    headset_update = get_headset_repository().update_pose(headset_id, position, orientation)

    if headset_update is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)

    else:
        return jsonify(headset_update), HTTPStatus.OK


@blueprint.route('/headsets/<headset_id>/poses', methods=['GET'])
async def get_headset_poses(headset_id):
    """
    Get headset poses
    ---
    get:
        summary: List headset poses
        description: >-
            List recorded headset poses (position and orientation).
        tags:
          - headsets
        parameters:
          - name: id
            in: path
            required: true
            description: Headset ID
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: incident
            in: query
            required: false
            description: Query poses from a specific incident ID.
        responses:
            200:
                description: A list of headset poses.
                content:
                    application/json:
                        schema:
                            type: array
                            items: HeadsetPose
    """
    headset = get_headset_repository().get_headset(headset_id)

    if headset is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist.", "severity": "Error"}),
            HTTPStatus.NOT_FOUND)

    query = request.args

    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    incident = query.get("incident", incident_handler.current_incident)
    headset_past_poses = headset.get_past_poses(headset_id, incident)

    if "envelope" in query:
        result = {query.get("envelope"): headset_past_poses}
    else:
        result = headset_past_poses

    return jsonify(result), HTTPStatus.OK


@blueprint.route('/headsets', methods=['POST'])
async def register():
    """
    Register a headset
    ---
    post:
        description: Register a headset
        tags:
          - headsets
        requestBody:
            required: true
            content:
                application/json:
                    schema: Headset
        responses:
            200:
                description: A headset
                content:
                    application/json:
                        schema: Headset
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
        tags:
          - headsets
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
    ---
    get:
        summary: List headset updates.
        description: >-
            List headset updates.

            The optional "after" and "wait" query parameters make it possible
            for the caller to wait for the next update by passing the last
            timestamp the caller has received.
        tags:
          - headsets
        parameters:
          - name: id
            in: path
            required: true
            description: Headset ID
          - name: after
            in: query
            required: false
            description: Limit results to updates after the given timestamp.
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: wait
            in: query
            required: false
            description: >-
                Request that the server wait a time limit (in seconds) for an
                update if none are immediately available. The server will
                return one or more results as soon as they are available, or if
                the time limit has passed, the server will return a No Content
                204 result indicating timeout. A time limit of 30-60 seconds is
                recommended.
        responses:
            200:
                description: A list of headset updates.
                content:
                    application/json:
                        schema:
                            type: array
                            items: HeadsetUpdate
            204:
                description: A waiting request timed out without any results.
    """
    headset = get_headset_repository().get_headset(headsetId)
    if headset is None:
        return {"message": "The requested headset does not exist."}, HTTPStatus.NOT_FOUND

    after = float(request.args.get("after", 0))

    updates = headset.get_updates(after=after)

    # Wait for new updates if the query returned no results and the caller
    # specified a wait timeout. If there are still no results, we return a
    # No-Content 204 code.
    wait = float(request.args.get("wait", 0))
    if len(updates) == 0 and wait > 0:
        try:
            future = headset.wait_for_headset_update()
            updates.append(await asyncio.wait_for(future, timeout=wait))
        except asyncio.TimeoutError:
            return jsonify([]), HTTPStatus.NO_CONTENT

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): updates}
    else:
        result = updates

    return jsonify(result)


@blueprint.route('/headsets/<headsetId>/updates', methods=['POST'])
async def update_position(headsetId):
    """
    Update a headset
    ---
    post:
        description: Create a new headset update
        tags:
          - headsets
        requestBody:
            required: true
            content:
                application/json:
                    schema: HeadsetUpdate
        responses:
            200:
                description: A headset update object
                content:
                    application/json:
                        schema: HeadsetUpdate
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


@blueprint.route('/headsets/<headset_id>', methods=['DELETE'])
async def delete_headset(headset_id):
    """
    Delete a headset
    ---
    delete:
        description: Delete a headset
        tags:
          - headsets
        parameters:
          - name: id
            in: path
            required: true
            description: Headset ID
        responses:
            200:
                description: Headset deleted
    """

    # TODO check authorization

    if not headset_id:
        return await make_response(jsonify({"message": "No map id", "severity": "Warning"}), HTTPStatus.BAD_REQUEST)

    deleted = get_headset_repository().remove_headset(headset_id)

    if deleted:
        return await make_response(jsonify({"message": "Headset deleted"}), HTTPStatus.OK)
    else:
        return await make_response(jsonify({"message": "Headset could not be deleted"}), HTTPStatus.BAD_REQUEST)


@blueprint.route('/headsets/<headsetId>', methods=['PUT'])
async def update_headset(headsetId):
    """
    Update a headset
    ---
    put:
        description: Update a headset
        tags:
          - headsets
        parameters:
          - name: id
            in: path
            required: true
            description: Headset ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Headset
        responses:
            200:
                description: New headset object
                content:
                    application/json:
                        schema: Headset
    """
    repo = get_headset_repository()
    if repo.get_headset(headsetId) is None:
        return await make_response(
            jsonify({"message": "The requested headset does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    body = await request.get_json()

    if 'name' in body:
        repo.update_headset_name(headsetId, body['name'])

    if 'position' in body and 'orientation' in body:
        repo.update_pose(headsetId, body['position'], body['orientation'])
    elif 'position' in body:
        repo.update_position(headsetId, body['position'])

    # headset was updated
    headset = repo.get_headset(headsetId)
    return jsonify(headset), HTTPStatus.OK


# @blueprint.route('/map-image/<mapId>', methods=['GET'])
# async def get_image(mapId):
#     folder_path = current_app.config['VIZAR_DATA_DIR'] + current_app.config['IMAGE_UPLOADS']
#     file_path = os.path.join(folder_path, f"{mapId}.jpeg")
#     print(f"Sending file {file_path}")
#     return await send_file(file_path, as_attachment=True)
