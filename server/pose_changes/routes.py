import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request
from werkzeug import exceptions

from server.resources.csvresource import CsvCollection


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
    """

    headset = g.active_incident.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    items = headset.PoseChange.find()

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): items}
    else:
        result = items

    return jsonify(result), HTTPStatus.OK


@pose_changes.route('/headsets/<headset_id>/pose-changes', methods=['POST'])
async def create_pose_change(headset_id):
    """
    Create headset pose changes
    ---
    post:
        summary: Create headset pose changes
        tags:
         - pose-changes
    """
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    incident_folder = g.active_incident.Headset.find_by_id(headset_id)
    if incident_folder is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    body = await request.get_json()

    change = incident_folder.PoseChange.load(body)
    incident_folder.PoseChange.add(change)

    # Also set the current position and orientation in the headset object.
    if body.get('position') is not None:
        headset.position = change.position
    if body.get('orientation') is not None:
        headset.orientation = change.orientation

    headset.updated = time.time()
    headset.save()

    return jsonify(change), HTTPStatus.CREATED
