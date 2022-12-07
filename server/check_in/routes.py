import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server import auth
from server.utils.response import maybe_wrap


check_ins = Blueprint('check-ins', __name__)


@check_ins.route('/headsets/<headset_id>/check-ins', methods=['GET'])
async def list_check_ins(headset_id):
    """
    List headset check-ins
    ---
    get:
        summary: List headset check-ins
        tags:
         - check-ins
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
                            items: CheckIn
    """

    headset = g.active_incident.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    items = headset.CheckIn.find()

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@check_ins.route('/headsets/<headset_id>/check-ins', methods=['POST'])
@auth.requires_own_headset_id
async def create_check_in(headset_id):
    """
    Create headset check-in
    ---
    post:
        summary: Create headset check-in
        tags:
         - check-ins
        requestBody:
            required: true
            content:
                application/json:
                    schema: CheckIn
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: CheckIn
    """
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    incident_folder = g.active_incident.Headset.find_by_id(headset_id)
    if incident_folder is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    body = await request.get_json()

    checkin = incident_folder.CheckIn.load(body, replace_id=True)
    checkin.save()

    # Also update relevant fields in the headset object.
    if body.get("location_id") is not None:
        headset.location_id = checkin.location_id

    headset.last_check_in_id = checkin.id
    headset.updated = time.time()
    headset.save()

    return jsonify(checkin), HTTPStatus.CREATED
