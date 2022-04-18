import asyncio
import json
import os
import time

from http import HTTPStatus

from quart import request, jsonify, make_response, Blueprint, current_app, send_file, g
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from server.headset.headsetrepository import get_headset_repository
from server.incidents.incident_handler import init_incidents_handler
from server.incidents.models import Incident
from server.utils.utils import GenericJsonEncoder, save_image

headsets = Blueprint('headsets', __name__)


@headsets.route('/headsets', methods=['GET'])
async def list_headsets():
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
    headsets = g.Headset.find()

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): headsets}
    else:
        result = headsets

    return jsonify(result), HTTPStatus.OK


@headsets.route('/headsets', methods=['POST'])
async def create_headset():
    """
    Create a headset
    ---
    post:
        description: Create a headset
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
    if body is None:
        body = {}

    # TODO: Finalize authentication method

    headset = g.Headset.load(body, replace_id=True)
    headset.save()

    folder = g.active_incident.Headset.add(headset.id)

    if 'position' in body or 'orientation' in body:
        change = folder.PoseChange.load(body)
        folder.PoseChange.add(change)

    return jsonify(headset), HTTPStatus.CREATED


@headsets.route('/headsets/<headset_id>', methods=['DELETE'])
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
                content:
                    application/json:
                        schema: Headset
    """

    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found".format(headset_id))

    # TODO check authorization

    headset.delete()

    folder = g.active_incident.Headset.find_by_id(headset_id)
    if folder is not None:
        folder.delete()

    return jsonify(headset), HTTPStatus.OK


@headsets.route('/headsets/<id>', methods=['GET'])
async def get_headset(id):
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
    headset = g.Headset.find_by_id(id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found".format(id))

    return jsonify(headset), HTTPStatus.OK


@headsets.route('/headsets/<headsetId>', methods=['PUT'])
async def replace_headset(headsetId):
    """
    Replace a headset
    ---
    put:
        description: Replace a headset
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
    body = await request.get_json()
    body['id'] = headsetId

    headset = g.Headset.load(body)
    headset.updated = time.time()
    created = headset.save()

    incident_folder = g.active_incident.Headset.find_by_id(headsetId)
    if incident_folder is None:
        incident_folder = g.active_incident.Headset.add(headset.id)

    if 'position' in body or 'orientation' in body:
        change = incident_folder.PoseChange.load(body)
        incident_folder.PoseChange.add(change)

    if created:
        return jsonify(headset), HTTPStatus.CREATED
    else:
        return jsonify(headset), HTTPStatus.OK


@headsets.route('/headsets/<headset_id>', methods=['PATCH'])
async def update_headset(headset_id):
    """
    Update a headset
    ---
    patch:
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
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found".format(id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    headset.update(body)
    headset.updated = time.time()
    headset.save()

    if 'position' in body or 'orientation' in body:
        folder = g.active_incident.Headset.find_by_id(headset_id)
        change = folder.PoseChange.load(body)
        folder.PoseChange.add(change)

    return jsonify(headset), HTTPStatus.OK


#
# The functions below are deprecated or in need of updating.
#


@headsets.route('/headsets/<headset_id>/poses', methods=['POST'])
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


@headsets.route('/headsets/<headset_id>/poses', methods=['GET'])
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


@headsets.route('/headsets/authenticate/', methods=['POST'])
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


@headsets.route('/headsets/<headsetId>/updates', methods=['GET'])
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


@headsets.route('/headsets/<headsetId>/updates', methods=['POST'])
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


@headsets.route('/image-upload/<imageId>', methods=['POST'])
async def upload(imageId):
    request_files = await request.files
    image = request_files['image']
    folder_path = current_app.config['VIZAR_DATA_DIR'] + current_app.config['IMAGE_UPLOADS']
    file_path = os.path.join(folder_path, str(secure_filename(image.filename)))
    await save_image(file_path, image)
    return await make_response({'success': 'true'})
