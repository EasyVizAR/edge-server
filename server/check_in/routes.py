import time
import uuid

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request
from werkzeug import exceptions

import sqlalchemy as sa

from server import auth
from server.headset.models import MobileDevice
from server.resources.filter import Filter
from server.utils.response import maybe_wrap

from .models import TrackingSession, CheckInSchema


check_in_schema = CheckInSchema()

check_ins = Blueprint('check-ins', __name__)


@check_ins.route('/headsets/<uuid:headset_id>/check-ins', methods=['GET'])
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
          - name: location_id
            in: query
            required: false
            schema:
                type: str
            description: Only show results from a given location.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: CheckIn
    """
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(TrackingSession).where(TrackingSession.mobile_device_id == headset_id)

        try:
            location_id = uuid.UUID(request.args.get('location_id'))
            stmt = stmt.where(TrackingSession.location_id == location_id)
        except:
            pass

        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(check_in_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@check_ins.route('/headsets/<uuid:headset_id>/check-ins', methods=['POST'])
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
    body = await request.get_json()
    body['headset_id'] = headset_id

    checkin = check_in_schema.load(body, transient=True)
    checkin.mobile_device_id = headset_id
    checkin.incident_id = g.active_incident_id

    async with g.session_maker() as session:
        session.add(checkin)
        await session.commit()

        device = await session.get(MobileDevice, headset_id)
        if device is None:
            raise exceptions.NotFound(description="Headset {} was not found".format(headset_id))

        device.location_id = checkin.location_id
        device.tracking_session_id = checkin.id
        await session.commit()

    result = check_in_schema.dump(checkin)

    return jsonify(result), HTTPStatus.CREATED


@check_ins.route('/headsets/<uuid:headset_id>/check-ins/<int:check_in_id>', methods=['DELETE'])
async def delete_check_in(headset_id, check_in_id):
    """
    Delete a headset check-in
    ---
    delete:
        description: Delete a headset check-in
        tags:
          - check-ins
        parameters:
          - name: headset_id
            in: path
            required: true
            description: Headset ID
          - name: check_in_id
            in: path
            required: true
            description: Headset check-in ID
        responses:
            200:
                description: Headset check-in deleted
                content:
                    application/json:
                        schema: CheckIn
    """
    async with g.session_maker() as session:
        stmt = sa.select(TrackingSession) \
                .where(TrackingSession.mobile_device_id == headset_id) \
                .where(TrackingSession.id == check_in_id)
        res = await session.execute(stmt)
        result = res.fetchone()

        if result is None:
            raise exceptions.NotFound(description="Headset {} check-in was not found".format(headset_id))

        stmt = sa.delete(TrackingSession) \
                .where(TrackingSession.mobile_device_id == headset_id) \
                .where(TrackingSession.id == check_in_id)
        await session.execute(stmt)
        await session.commit()

    checkin = check_in_schema.dump(result)

    return jsonify(checkin), HTTPStatus.OK


@check_ins.route('/locations/<uuid:location_id>/check-ins', methods=['GET'])
async def list_location_check_ins(location_id):
    """
    List location check-ins
    ---
    get:
        summary: List location check-ins
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
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(TrackingSession) \
                .where(TrackingSession.location_id == location_id)

        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(check_in_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK
