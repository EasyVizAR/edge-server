import asyncio
import datetime
import os
import time
import uuid

from http import HTTPStatus

import pyqrcode

from quart import request, jsonify, Blueprint, current_app, g, send_from_directory
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server.check_in.models import TrackingSession
from server.pose_changes.models import DevicePose, PoseChangeSchema
from server.resources.filter import Filter
from server.resources.geometry import Vector3f, Vector4f
from server.utils.patch import patch_object
from server.utils.response import maybe_wrap

from .models import MobileDevice, HeadsetSchema

headsets = Blueprint('headsets', __name__)

headset_schema = HeadsetSchema()
pose_change_schema = PoseChangeSchema()


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
        responses:
            200:
                description: A list of headsets.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Headset
    """
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice)

        try:
            location_id = uuid.UUID(request.args.get('location_id'))
            stmt = stmt.where(MobileDevice.location_id == location_id)
        except:
            pass

        name = request.args.get('name')
        if name is not None:
            stmt = stmt.where(MobileDevice.name == name)

        since = request.args.get('since')
        if since is not None:
            stmt = stmt.where(MobileDevice.updated_time > since)

        until = request.args.get('until')
        if until is not None:
            stmt = stmt.where(MobileDevice.updated_time < until)

        stmt = stmt.options(sa.orm.selectinload(MobileDevice.pose))
        stmt = stmt.options(sa.orm.selectinload(MobileDevice.navigation_target))

        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(headset_schema.dump(row))

    await current_app.dispatcher.dispatch_event("headsets:viewed", "/headsets")

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


async def _create_headset(headset_id, body):
    # Choose a color for the headset by cycling through the palette.
    if body.get("color") in [None, ""]:
        body['color'] = default_color_palette[headset_id.int % len(default_color_palette)]

    body['id'] = headset_id
    headset = headset_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
    headset.pose = None

    async with g.session_maker() as session:
        # If the headset is created with location_id set, we can automatically
        # create a check-in record for the headset at that location.
        if headset.location_id is not None:
            checkin = TrackingSession(
                mobile_device_id=headset.id,
                incident_id=g.active_incident_id,
                location_id=headset.location_id
            )
            session.add(checkin)
            await session.flush()

            headset.tracking_session_id = checkin.id

            # If we have created a TrackingSession and also have position and
            # orientation defined, we can create a DevicePose record.
            if 'position' in body and 'orientation' in body:
                pose = pose_change_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
                pose.tracking_session_id = checkin.id
                pose.mobile_device_id = headset.id
                session.add(pose)

                headset.device_pose_id = pose.id
                headset.pose = pose

        session.add(headset)
        await session.commit()

    result = headset_schema.dump(headset)

    # Create a private copy of the headset including the authentication token
    # and return that one to the caller.
    private_result = headset_schema.dump(headset)
    private_result['token'] = headset.token

    await current_app.dispatcher.dispatch_event("headsets:created",
            "/headsets/"+result['id'], current=result)
    if headset.location_id is not None:
        await current_app.dispatcher.dispatch_event("location-headsets:created",
                "/locations/{}/headsets/{}".format(str(headset.location_id), result['id']), current=result)

    return private_result


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

    result = await _create_headset(uuid.uuid4(), body)
    return jsonify(result), HTTPStatus.CREATED


@headsets.route('/headsets/<uuid:headset_id>', methods=['DELETE'])
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
    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice) \
                .where(MobileDevice.id == headset_id) \
                .limit(1) \
                .options(sa.orm.selectinload(MobileDevice.pose))

        result = await session.execute(stmt)
        headset = result.scalar()
        if headset is None:
            raise exceptions.NotFound(description="Headset {} was not found".format(id))

        await session.delete(headset)
        await session.commit()

    result = headset_schema.dump(headset)

    await current_app.dispatcher.dispatch_event("headsets:deleted", "/headsets/"+result['id'], previous=result)
    if headset.location_id is not None:
        await current_app.dispatcher.dispatch_event("location-headsets:deleted",
                "/locations/{}/headsets/{}".format(headset.location_id, headset.id), previous=result)
    return jsonify(result), HTTPStatus.OK


@headsets.route('/headsets/<uuid:headset_id>', methods=['GET'])
async def get_headset(headset_id):
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
    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice) \
                .where(MobileDevice.id == headset_id) \
                .limit(1) \
                .options(sa.orm.selectinload(MobileDevice.pose))

        result = await session.execute(stmt)
        headset = result.scalar()
        if headset is None:
            raise exceptions.NotFound(description="Headset {} was not found".format(id))

    result = headset_schema.dump(headset)

    await current_app.dispatcher.dispatch_event("headsets:viewed", "/headsets/"+result['id'], current=result)
    return jsonify(result), HTTPStatus.OK


@headsets.route('/headsets/<uuid:headset_id>', methods=['PUT'])
async def replace_headset(headset_id):
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
                description: The new object
                content:
                    application/json:
                        schema: Headset
    """
    body = await request.get_json()
    if body is None:
        body = {}
    body['id'] = headset_id

    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice) \
                .where(MobileDevice.id == headset_id) \
                .limit(1) \
                .options(sa.orm.selectinload(MobileDevice.pose)) \
                .options(sa.orm.selectinload(MobileDevice.navigation_target))

        result = await session.execute(stmt)
        existing = result.scalar()

    if existing is None:
        result = await _create_headset(headset_id, body)
        return jsonify(result), HTTPStatus.CREATED

    else:
        result = await _update_headset(headset_id, body)
        return jsonify(result), HTTPStatus.OK


async def _update_headset(headset_id, patch):
    stmt = sa.select(MobileDevice) \
            .where(MobileDevice.id == headset_id) \
            .limit(1) \
            .options(sa.orm.selectinload(MobileDevice.pose)) \
            .options(sa.orm.selectinload(MobileDevice.navigation_target))

    result = await g.session.execute(stmt)
    device = result.scalar()
    if device is None:
        raise exceptions.NotFound(description="Headset {} was not found".format(id))

    previous = headset_schema.dump(device)
    device.update(patch)

    if patch.get('location_id') is not None:
        location_id = uuid.UUID(patch['location_id'])
        if location_id != device.location_id:
            checkin = TrackingSession(
                mobile_device_id=device.id,
                incident_id=g.active_incident_id,
                location_id=location_id
            )
            g.session.add(checkin)
            await g.session.flush()

            device.location_id = location_id
            device.tracking_session_id = checkin.id

    # If we have a valid location set and the caller provided a
    # position and orientation, we can create a DevicePose record.
    if device.tracking_session_id is not None and 'position' in patch and 'orientation' in patch:
        pose = pose_change_schema.load(patch, transient=True, unknown=marshmallow.EXCLUDE)
        pose.tracking_session_id = device.tracking_session_id
        pose.mobile_device_id = device.id
        g.session.add(pose)
        await g.session.flush()

        device.device_pose_id = pose.id
        device.pose = pose

    device.updated_time = datetime.datetime.now()

    await g.session.commit()

    result = headset_schema.dump(device)

    await current_app.dispatcher.dispatch_event("headsets:updated",
            "/headsets/"+str(device.id), current=result, previous=previous)
    if device.location_id is not None:
        await current_app.dispatcher.dispatch_event("location-headsets:updated",
                "/locations/{}/headsets/{}".format(result['location_id'], str(device.id)), current=result, previous=previous)

    return result


@headsets.route('/headsets/<uuid:headset_id>', methods=['PATCH'])
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
    result = await _update_headset(headset_id, body)
    return jsonify(result), HTTPStatus.OK


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
    if incident_id == "active":
        incident_id = g.active_incident_id
    else:
        try:
            incident_id = uuid.UUID(incident_id)
        except:
            raise exceptions.BadRequest('Could not parse string "{}" as a UUID'.format(incident_id))

    items = []
    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice) \
                .join(TrackingSession, TrackingSession.id == MobileDevice.tracking_session_id) \
                .where(TrackingSession.incident_id == incident_id) \
                .options(sa.orm.selectinload(MobileDevice.pose))

        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(headset_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@headsets.route('/headsets/<uuid:headset_id>/qrcode', methods=['GET'])
async def get_headset_qrcode(headset_id):
    """
    Get a QR code for the device.
    ---
    get:
        description: Get a QR code for the device.
        tags:
          - locations
        parameters:
          - name: id
            in: path
            required: true
            description: Location ID
        responses:
            200:
                description: An SVG image file.
                content:
                    image/svg+xml: {}
    """
    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice) \
                .where(MobileDevice.id == headset_id) \
                .limit(1)

        result = await session.execute(stmt)
        headset = result.scalar()
        if headset is None:
            raise exceptions.NotFound(description="Headset {} was not found".format(id))

        filename = "{}-qrcode.svg".format(headset_id.hex)
        path = os.path.join(g.temp_dir, filename)

        url = 'vizar://{}/devices/{}?token={}'.format(request.host, headset_id, headset.token)
        code = pyqrcode.create(url, error='L')
        code.svg(path, title=url, scale=16)

    return await send_from_directory(g.temp_dir, filename)
