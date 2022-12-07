import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.resources.csvresource import CsvCollection

from server.utils.response import maybe_wrap


pose_changes = Blueprint('pose-changes', __name__)


@pose_changes.route('/headsets/<headset_id>/pose-changes', methods=['GET'])
async def list_pose_changes(headset_id):
    """
    List headset pose changes
    ---
    get:
        summary: List headset pose changes
        tags:
         - pose-changes
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: PoseChange
    """
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    incident_folder = g.active_incident.Headset.find_by_id(headset_id)
    if incident_folder is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    if headset.last_check_in_id is None:
        raise exceptions.NotFound(description="Headset {} has never checked in".format(headset_id))

    checkin = incident_folder.CheckIn.find_by_id(headset.last_check_in_id)
    if checkin is None:
        raise exceptions.NotFound(description="Headset {} check-in record was not found".format(headset_id))

    items = checkin.PoseChange.find()

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@pose_changes.route('/headsets/<headset_id>/pose-changes.csv', methods=['GET'])
async def list_pose_changes_csv(headset_id):
    """
    List headset pose changes (CSV file)
    ---
    get:
        summary: List headset pose changes (CSV file)
        tags:
         - pose-changes
        responses:
            200:
                description: A list of pose changes in CSV
                content:
                    text/csv
    """
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    incident_folder = g.active_incident.Headset.find_by_id(headset_id)
    if incident_folder is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    if headset.last_check_in_id is None:
        raise exceptions.NotFound(description="Headset {} has never checked in".format(headset_id))

    checkin = incident_folder.CheckIn.find_by_id(headset.last_check_in_id)
    if checkin is None:
        raise exceptions.NotFound(description="Headset {} check-in record was not found".format(headset_id))

    # Pose changes are stored in a CSV file, so send the file directly without
    # processing.
    return await send_from_directory(checkin.PoseChange.base_directory, checkin.PoseChange.collection_filename)


@pose_changes.route('/headsets/<headset_id>/pose-changes', methods=['POST'])
async def create_pose_change(headset_id):
    """
    Create headset pose change
    ---
    post:
        summary: Create headset pose change
        tags:
         - pose-changes
        requestBody:
            required: true
            content:
                application/json:
                    schema: PoseChange
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: PoseChange
    """
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    incident_folder = g.active_incident.Headset.find_by_id(headset_id)
    if incident_folder is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    if headset.last_check_in_id is None:
        raise exceptions.NotFound(description="Headset {} has never checked in".format(headset_id))

    checkin = incident_folder.CheckIn.find_by_id(headset.last_check_in_id)
    if checkin is None:
        raise exceptions.NotFound(description="Headset {} check-in record was not found".format(headset_id))

    body = await request.get_json()

    change = checkin.PoseChange.load(body)
    checkin.PoseChange.add(change)

    # Also set the current position and orientation in the headset object.
    if body.get('position') is not None:
        headset.position = change.position
    if body.get('orientation') is not None:
        headset.orientation = change.orientation

    headset.updated = time.time()
    headset.save()

    return jsonify(change), HTTPStatus.CREATED
