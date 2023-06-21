import asyncio
import time

from http import HTTPStatus

from quart import request, jsonify, Blueprint, current_app, g
from werkzeug import exceptions

from server.pose_changes.models import PoseChange
from server.resources.filter import Filter

from .models import RegisteredHeadsetModel

headsets = Blueprint('headsets', __name__)


# Color palette for headsets.  This is the Tol palette, which is
# distinguishable for colorblind vision.
default_color_palette = [
    "#4477aa",
    "#ee6677",
    "#228833",
    "#ccbb44",
    "#66ccee",
    "#aa3377",
    "#bbbbbb"
]


@headsets.route('/headsets', methods=['GET'])
async def list_headsets():
    """
    List headsets
    ---
    get:
        summary: List headsets
        description: |-
            The following example queries for headsets with on unspecified
            or unknown location.

                GET /headsets?location_id=none

            The following example queries for headsets at a given location.

                GET /headsets?location_id=28c68ff7-0655-4392-a218-ecc6645191c2
        tags:
          - headsets
        parameters:
          - name: envelope
            in: query
            required: false
            schema:
                type: str
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: location_id
            in: query
            required: false
            schema:
                type: str
            description: Only show headsets present in a given location or unknown location if set to "none".
          - name: name
            in: query
            required: false
            schema:
                type: str
            description: >-
                Filter items based on name.

                Wildcards (*) and single character matching (?) are supported.
                For example, a query of "Test Headset *" would match "Test
                Headset 1" and "Test Headset 20".
          - name: since
            in: query
            required: false
            schema:
                type: float
            description: Only show items that were created or updated since this time.
          - name: until
            in: query
            required: false
            schema:
                type: float
            description: Only show items that were created or updated before this time.
          - name: wait
            in: query
            required: false
            schema:
                type: float
            description: >-
                Request that the server wait a time limit (in seconds) for a
                new result if none are immediately available. The server will
                return one or more results as soon as they are available, or if
                the time limit has passed, the server will return a No Content
                204 result indicating timeout. A time limit of 30-60 seconds is
                recommended.
        responses:
            200:
                description: A list of headsets.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Headset
    """
    filt = Filter()
    if "location_id" in request.args:
        location_id = request.args.get("location_id").lower()
        if location_id in ["", "none", "null"]:
            location_id = None
        filt.target_equal_to("location_id", location_id)
    if "name" in request.args:
        filt.target_string_match("name", request.args.get("name"))
    if "since" in request.args:
        filt.target_greater_than("updated", float(request.args.get("since")))
    if "until" in request.args:
        filt.target_less_than("updated", float(request.args.get("until")))

    items = g.Headset.find(filt=filt)

    # Wait for new objects if the query returned no results and the caller
    # specified a wait timeout. If there are still no results, we return a 204
    # No Content code.
    wait = float(request.args.get("wait", 0))
    if len(items) == 0 and wait > 0:
        try:
            item = await asyncio.wait_for(g.Headset.wait_for(filt=filt), timeout=wait)
            items.append(item)
        except asyncio.TimeoutError:
            return jsonify([]), HTTPStatus.NO_CONTENT

    # Wrap the results list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): items}
    else:
        result = items

    await current_app.dispatcher.dispatch_event("headsets:viewed", "/headsets")
    return jsonify(result), HTTPStatus.OK


@headsets.route('/headsets', methods=['POST'])
async def create_headset():
    """
    Create a headset
    ---
    post:
        summary: Create a headset
        description: |-
            Use this method to register a new headset. Headsets persist across
            incidents and locations on the server, so outside of testing and
            development, this should only need to be called once on the first
            time a physical device connects to a particular edge server.

            Most important is passing a descriptive name that differentiates
            the headsets from others on the server. If the location and
            position are known, those can be set during registration or later
            on through an update.

            The following example creates a headset with a known location,
            position, and orientation.

                POST /headsets
                Content-Type: application/json
                {
                    "name": "Lance's Headset",
                    "location_id": "28c68ff7-0655-4392-a218-ecc6645191c2",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0, "w": 0}
                }

            The server responds with the created headset object, which
            most importantly, contains the new headset ID, which can be
            in subsequent operations.

                201 CREATED
                Content-Type: application/json
                {
                    "id": "207f24fb-558f-4d34-953a-8f7765f25069",
                    ...
                }
        tags:
          - headsets
        requestBody:
            required: true
            content:
                application/json:
                    schema: Headset
        responses:
            201:
                description: A headset
                content:
                    application/json:
                        schema: RegisteredHeadset
    """
    body = await request.get_json()
    if body is None:
        body = {}

    # Choose a color for the headset by cycling through the palette.
    if body.get("color") in [None, ""]:
        headsets = g.active_incident.Headset.find()
        n = len(headsets)
        body['color'] = default_color_palette[n % len(default_color_palette)]

    # TODO: Finalize authentication method

    headset = g.Headset.load(body, replace_id=True)
    headset.save()

    folder = g.active_incident.Headset.add(headset.id)

    # If the headset is created with location_id set, we can automatically
    # create a check-in record for the headset at that location.
    if headset.location_id is not None:
        checkin = folder.CheckIn.load({'location_id': headset.location_id}, replace_id=True)
        checkin.save()

        headset.last_check_in_id = checkin.id
        headset.save()

        if 'position' in body and 'orientation' in body:
            change = PoseChange(
                    incident_id=g.active_incident.id,
                    headset_id=headset.id,
                    check_in_id=checkin.id,
                    position=headset.position,
                    orientation=headset.orientation
            )

            async with g.session_maker() as session:
                session.add(change)
                await session.commit()

    tmp = headset.Schema().dump(headset)
    rheadset = RegisteredHeadsetModel.Schema().load(tmp)

    rheadset.token = g.authenticator.create_headset_token(headset.id)
    g.authenticator.save()

    await current_app.dispatcher.dispatch_event("headsets:created",
            "/headsets/"+headset.id, current=headset)
    if headset.location_id is not None:
        await current_app.dispatcher.dispatch_event("location-headsets:created",
                "/locations/{}/headsets/{}".format(headset.location_id, headset.id), current=headset)
    return jsonify(rheadset), HTTPStatus.CREATED


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

    await current_app.dispatcher.dispatch_event("headsets:deleted", "/headsets/"+headset.id, previous=headset)
    if headset.location_id is not None:
        await current_app.dispatcher.dispatch_event("location-headsets:deleted",
                "/locations/{}/headsets/{}".format(headset.location_id, headset.id), previous=headset)
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

    await current_app.dispatcher.dispatch_event("headsets:viewed", "/headsets/"+headset.id, current=headset)
    return jsonify(headset), HTTPStatus.OK


def valid_check_in_or_none(incident_folder, previous, current):
    if current.last_check_in_id is None:
        return None

    # Triggers a new check-in if the headset left its location and returned
    if previous.location_id is None:
        return None

    checkin = incident_folder.CheckIn.find_by_id(current.last_check_in_id)
    if checkin is None or checkin.location_id != current.location_id:
        return None

    return checkin


@headsets.route('/headsets/<headsetId>', methods=['PUT'])
async def replace_headset(headsetId):
    """
    Replace a headset
    ---
    put:
        summary: Replace a headset
        description: |-
            Please note this is a full create or replace operation that
            expects all fields to be set in the request body. For a partial
            update operation, please use the PATCH operation instead.
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

    previous = g.Headset.find_by_id(headsetId)

    incident_folder = g.active_incident.Headset.find_by_id(headsetId)
    if incident_folder is None:
        incident_folder = g.active_incident.Headset.add(headset.id)

    checkin = valid_check_in_or_none(incident_folder, previous, headset)

    # Automatically create a check-in record for this headset
    if checkin is None and headset.location_id != None:
        checkin = incident_folder.CheckIn.load({'location_id': headset.location_id}, replace_id=True)
        checkin.save()

        headset.last_check_in_id = checkin.id

    if checkin is not None and ('position' in body or 'orientation' in body):
        change = PoseChange(
                incident_id=g.active_incident.id,
                headset_id=headset.id,
                check_in_id=checkin.id,
                position=headset.position,
                orientation=headset.orientation
        )

        async with g.session_maker() as session:
            session.add(change)
            await session.commit()

    created = headset.save()

    if created:
        await current_app.dispatcher.dispatch_event("headsets:created",
                "/headsets/"+headset.id, current=headset, previous=previous)
        if headset.location_id is not None:
            await current_app.dispatcher.dispatch_event("location-headsets:created",
                    "/locations/{}/headsets/{}".format(headset.location_id, headset.id), current=headset, previous=previous)
        return jsonify(headset), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("headsets:updated",
                "/headsets/"+headset.id, current=headset, previous=previous)
        if headset.location_id is not None:
            await current_app.dispatcher.dispatch_event("location-headsets:updated",
                    "/locations/{}/headsets/{}".format(headset.location_id, headset.id), current=headset, previous=previous)
        return jsonify(headset), HTTPStatus.OK


async def _update_headset(headset_id, patch):
    headset = g.Headset.find_by_id(headset_id)
    if headset is None:
        raise exceptions.NotFound(description="Headset {} was not found".format(id))

    previous = headset.clone()

    # Do not allow changing the object's ID
    if 'id' in patch:
        del patch['id']

    headset.update(patch)
    headset.updated = time.time()

    folder = g.active_incident.Headset.find_by_id(headset_id)
    if folder is None:
        # This is the first time the headset appears under the current incident.
        folder = g.active_incident.Headset.add(headset.id)

    checkin = valid_check_in_or_none(folder, previous, headset)

    # Automatically create a check-in record for this headset
    if checkin is None and headset.location_id != None:
        checkin = folder.CheckIn.load({'location_id': headset.location_id}, replace_id=True)
        checkin.save()

        headset.last_check_in_id = checkin.id

    if checkin is not None and ('position' in patch or 'orientation' in patch):
        change = PoseChange(
                incident_id=g.active_incident.id,
                headset_id=headset_id,
                check_in_id=checkin.id,
                position=headset.position,
                orientation=headset.orientation
        )

        async with g.session_maker() as session:
            session.add(change)
            await session.commit()

    headset.save()

    await current_app.dispatcher.dispatch_event("headsets:updated",
            "/headsets/"+headset.id, current=headset, previous=previous)
    if headset.location_id is not None:
        await current_app.dispatcher.dispatch_event("location-headsets:updated",
                "/locations/{}/headsets/{}".format(headset.location_id, headset.id), current=headset, previous=previous)

    return headset


@headsets.route('/headsets/<headset_id>', methods=['PATCH'])
async def update_headset(headset_id):
    """
    Update a headset
    ---
    patch:
        summary: Update a headset
        description: |-
            This can be used to selectively update fields in the headset
            record.

            Here is an example that sets the headset's current location,
            position, and orientation but would not affect other fields
            such as the name.

                PATCH /headsets/207f24fb-558f-4d34-953a-8f7765f25069
                Content-Type: application/json
                {
                    "location_id": "28c68ff7-0655-4392-a218-ecc6645191c2",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0, "w": 0}
                }

            If position and/or orientation are altered through this method, a
            side effect is that a pose change record will also be created,
            which would be apparent in the following request.

                GET /headsets/207f24fb-558f-4d34-953a-8f7765f25069/pose-changes
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
    headset = await _update_headset(headset_id, body)
    return jsonify(headset), HTTPStatus.OK


@headsets.route('/incidents/<incident_id>/headsets', methods=['GET'])
async def list_incident_headsets(incident_id):
    """
    List headsets involved in an incident
    ---
    get:
        summary: List headsets involved in an incident
        description: |-
            This method may be used to find only the headsets that were active
            in a particular incident, including the currently active incident.
            The string "active" serves as an alias for the ID of the active
            incident.

            Example:

                GET /incidents/active/headsets
        tags:
          - headsets
        parameters:
          - name: incident_id
            in: path
            required: true
            schema:
                type: str
            description: Incident ID or "active" for the active incident.
          - name: envelope
            in: query
            required: false
            schema:
                type: str
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
    incident_id = incident_id.lower()
    if incident_id == "active":
        incident = g.active_incident
    else:
        incident = g.Incident.find_by_id(incident_id)

    if incident is None:
        raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

    headsets = []

    # Find the headset IDs which have records in the incident folder.
    # Then use the headset ID to find the headset object.
    for incid_headset in incident.Headset.find():
        headset = g.Headset.find_by_id(incid_headset.id)
        if headset is not None:
            headsets.append(headset)

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): headsets}
    else:
        result = headsets

    return jsonify(result), HTTPStatus.OK
