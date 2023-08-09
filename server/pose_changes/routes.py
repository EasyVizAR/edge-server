import time

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from quart.helpers import stream_with_context
from werkzeug import exceptions

import sqlalchemy as sa

from server.utils.rate_limiter import rate_limit_expensive
from server.utils.response import maybe_wrap

from .models import PoseChange, PoseChangeSchema


pose_changes = Blueprint('pose-changes', __name__)


@pose_changes.route('/headsets/<headset_id>/pose-changes', methods=['GET'])
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

    schema = PoseChangeSchema()

    items = []
    async with g.session_maker() as session:
        stmt = sa.select(PoseChange) \
                .where(PoseChange.headset_id == headset_id) \
                .order_by(PoseChange.id.desc()) \
                .limit(limit)
        result = await session.execute(stmt)
        for c in result.scalars():
            dump = schema.dump(c)
            items.append(dump)

    # We sorted in descending order to find the last N rows.
    # Now return the list to expected chronological order.
    items.reverse()

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


async def do_list_check_in_pose_changes(headset_id, check_in_id, limit=None):
    schema = PoseChangeSchema()

    items = []
    async with g.session_maker() as session:
        stmt = sa.select(PoseChange) \
                .where(PoseChange.headset_id == headset_id) \
                .where(PoseChange.check_in_id == check_in_id) \
                .order_by(PoseChange.id.desc()) \
                .limit(limit)
        result = await session.execute(stmt)
        for c in result.scalars():
            dump = schema.dump(c)
            items.append(dump)

    # We sorted in descending order to find the last N rows.
    # Now return the list to expected chronological order.
    items.reverse()

    return items


@pose_changes.route('/headsets/<headset_id>/check-ins/<check_in_id>/pose-changes', methods=['GET'])
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


@pose_changes.route('/headsets/<headset_id>/check-ins/<check_in_id>/pose-changes/replay', methods=['POST'])
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

    incident_folder = g.active_incident.Headset.find_by_id(headset_id)
    if incident_folder is None:
        raise exceptions.NotFound(description="Headset {} was not found in the current incident".format(headset_id))

    checkin = incident_folder.CheckIn.find_by_id(check_in_id)
    if checkin is None:
        raise exceptions.NotFound(description="Headset {} check-in was not found".format(headset_id))

    location = g.active_incident.Location.find_by_id(checkin.location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(checkin.location_id))

    items = await do_list_check_in_pose_changes(headset_id, check_in_id, limit=limit)

    current_app.navigator.add_trace(location, items)

    return jsonify({}), HTTPStatus.OK


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
    header = "incident_id,check_in_id,time,position.x,position.y,position.z,orientation.x,orientation.y,orientation.z,orientation.w\n"

    session_maker = g.session_maker

    @stream_with_context
    async def csv_generator():
        yield header

        async with session_maker() as session:
            stmt = sa.select(PoseChange) \
                    .where(PoseChange.headset_id == headset_id) \
                    .order_by(PoseChange.time)
            result = await session.execute(stmt)
            for c in result.scalars():
                values = [
                    c.incident_id,
                    c.check_in_id,
                    c.time,
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

    schema = PoseChangeSchema()

    body = await request.get_json()
    change = schema.load(body, transient=True)
    change.headset_id = headset_id

    if "incident_id" not in body:
        change.incident_id = g.active_incident.id
    if "check_in_id" not in body:
        change.check_in_id = headset.last_check_in_id

    async with g.session_maker() as session:
        session.add(change)
        await session.commit()

    result = schema.dump(change)

    # Also set the current position and orientation in the headset object.
    if body.get('position') is not None:
        headset.position = change.position
    if body.get('orientation') is not None:
        headset.orientation = change.orientation

    headset.updated = time.time()
    headset.save()

    return jsonify(result), HTTPStatus.CREATED
