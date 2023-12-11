import datetime
import time
import uuid

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from quart.helpers import stream_with_context
from werkzeug import exceptions

import sqlalchemy as sa

from server.headset.models import MobileDevice
from server.models.locations import Location
from server.models.tracking_sessions import TrackingSession
from server.utils.rate_limiter import rate_limit_expensive
from server.utils.response import maybe_wrap

from .models import DevicePose, PoseChangeSchema


pose_changes = Blueprint('pose-changes', __name__)

pose_change_schema = PoseChangeSchema()


@pose_changes.route('/headsets/<uuid:headset_id>/pose-changes', methods=['GET'])
@rate_limit_expensive
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
          - name: limit
            in: query
            required: false
            description: If set, limit the number of values returned.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: PoseChange
    """
    limit = None
    if "limit" in request.args:
        limit = int(request.args.get("limit"))

    items = []
    async with g.session_maker() as session:
        stmt = sa.select(DevicePose) \
                .where(DevicePose.mobile_device_id == headset_id) \
                .order_by(DevicePose.id.desc()) \
                .limit(limit)

        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(pose_change_schema.dump(row))

    # We sorted in descending order to find the last N rows.
    # Now return the list to expected chronological order.
    items.reverse()

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


async def do_list_check_in_pose_changes(headset_id, check_in_id, limit=None):
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(DevicePose) \
                .where(DevicePose.mobile_device_id == headset_id) \
                .where(DevicePose.tracking_session_id == check_in_id) \
                .order_by(DevicePose.id.desc()) \
                .limit(limit)
        result = await session.execute(stmt)
        for c in result.scalars():
            dump = pose_change_schema.dump(c)
            items.append(dump)

    # We sorted in descending order to find the last N rows.
    # Now return the list to expected chronological order.
    items.reverse()

    return items


@pose_changes.route('/headsets/<uuid:headset_id>/check-ins/<int:check_in_id>/pose-changes', methods=['GET'])
async def list_check_in_pose_changes(headset_id, check_in_id):
    """
    List headset pose changes for a specified check-in
    ---
    get:
        summary: List headset pose changes for a specified check-in
        tags:
         - pose-changes
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: limit
            in: query
            required: false
            description: If set, limit the number of values returned.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: PoseChange
    """
    limit = None
    if "limit" in request.args:
        limit = int(request.args.get("limit"))

    items = await do_list_check_in_pose_changes(headset_id, check_in_id, limit=limit)

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@pose_changes.route('/headsets/<uuid:headset_id>/check-ins/<int:check_in_id>/pose-changes/replay', methods=['POST'])
async def replay_check_in_pose_changes(headset_id, check_in_id):
    """
    Replay headset pose changes for a specified check-in
    ---
    post:
        summary: Replay headset pose changes for a specified check-in
        description: |
            This method loads the pose changes for a specified check-in
            and processes the trace as if it had just been received
            by a headset for map construction purposes.

            Generally, mapping from data collected in real-time should
            suffice. However, this can be useful for testing or
            rebuilding a floor map that had errors.

        tags:
         - pose-changes
        parameters:
          - name: limit
            in: query
            required: false
            description: If set, limit the number of values considered.
        responses:
            200:
    """
    limit = None
    if "limit" in request.args:
        limit = int(request.args.get("limit"))

    async with g.session_maker() as session:
        stmt = sa.select(Location) \
                .join(TrackingSession) \
                .where(TrackingSession.mobile_device_id == headset_id) \
                .where(TrackingSession.id == check_in_id) \
                .limit(1)
        result = await session.execute(stmt)
        location = result.scalar()

        if location is None:
            raise exceptions.NotFound("No location found for mobile device {} and tracking session {}".format(headset_id, check_in_id))

    items = await do_list_check_in_pose_changes(headset_id, check_in_id, limit=limit)

    current_app.navigator.add_trace(location, items)

    return jsonify({}), HTTPStatus.OK


@pose_changes.route('/headsets/<uuid:headset_id>/pose-changes.csv', methods=['GET'])
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
    header = "incident_id,check_in_id,time,position.x,position.y,position.z,orientation.x,orientation.y,orientation.z,orientation.w\n"

    session_maker = g.session_maker

    @stream_with_context
    async def csv_generator():
        yield header

        async with session_maker() as session:
            stmt = sa.select(DevicePose) \
                    .where(DevicePose.mobile_device_id == headset_id) \
                    .order_by(DevicePose.id)
            result = await session.execute(stmt)
            for c in result.scalars():
                values = [
                    "",
                    c.tracking_session_id,
                    c.created_time.timestamp(),
                    c.position_x,
                    c.position_y,
                    c.position_z,
                    c.orientation_x,
                    c.orientation_y,
                    c.orientation_z,
                    c.orientation_w
                ]
                yield ",".join(str(v) for v in values) + "\n"

    headers = {
        'Content-Type': 'text/csv'
    }
    return csv_generator(), 200, headers


@pose_changes.route('/headsets/<uuid:headset_id>/tracking-sessions/<int:tracking_session_id>/pose-changes.csv', methods=['GET'])
async def list_tracking_session_pose_changes_csv(headset_id, tracking_session_id):
    """
    List headset pose changes for a single tracking session (CSV file)
    ---
    get:
        summary: List headset pose changes for a single tracking session (CSV file)
        tags:
         - pose-changes
        responses:
            200:
                description: A list of pose changes in CSV
                content:
                    text/csv
    """
    header = "time,position.x,position.y,position.z,orientation.x,orientation.y,orientation.z,orientation.w\n"

    session_maker = g.session_maker

    @stream_with_context
    async def csv_generator():
        yield header

        async with session_maker() as session:
            stmt = sa.select(DevicePose) \
                    .where(DevicePose.mobile_device_id == headset_id) \
                    .where(DevicePose.tracking_session_id == tracking_session_id) \
                    .order_by(DevicePose.id)
            result = await session.execute(stmt)
            for c in result.scalars():
                values = [
                    c.created_time.timestamp(),
                    c.position_x,
                    c.position_y,
                    c.position_z,
                    c.orientation_x,
                    c.orientation_y,
                    c.orientation_z,
                    c.orientation_w
                ]
                yield ",".join(str(v) for v in values) + "\n"

    disposition = 'attachment; filename="pose-changes-{}.csv"'.format(tracking_session_id)
    headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': disposition
    }
    return csv_generator(), 200, headers


@pose_changes.route('/headsets/<uuid:headset_id>/pose-changes', methods=['POST'])
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
    body = await request.get_json()

    async with g.session_maker() as session:
        stmt = sa.select(MobileDevice).where(MobileDevice.id == headset_id).limit(1)
        result = await session.execute(stmt)
        headset = result.scalar()
        if headset is None:
            raise exceptions.NotFound(description="Headset {} was not found".format(headset_id))

        pose = pose_change_schema.load(body, transient=True)
        pose.mobile_device_id = headset_id
        pose.tracking_session_id = headset.tracking_session_id
        session.add(pose)
        await session.flush()

        headset.device_pose_id = pose.id
        headset.update_time = datetime.datetime.now()
        await session.commit()

    result = pose_change_schema.dump(pose)

    # TODO send headset updated message

    return jsonify(result), HTTPStatus.CREATED
