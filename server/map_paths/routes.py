import datetime
import uuid

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server import auth
from server.utils.response import maybe_wrap

from .models import MapPath, MapPathSchema


map_paths = Blueprint("map-paths", __name__)
map_path_schema = MapPathSchema()


# Compatibility fix for Unity JsonUtility, which does not support nested
# lists.  If requested, convert to dict with x, y or x, y, z keys. This is
# not really an efficient representation, unfortunately.
INFLATE_VECTORS = True


def inflate_vectors(points):
    new_points = []
    for i, point in enumerate(points):
        if isinstance(point, list):
            new_points.append(dict(zip(["x", "y", "z"], point)))
        else:
            new_points.append(point)

    return new_points


def ingest_point_list(points):
    """
    Ensure that the list contains points which are lists of floats
    rather than {x,y,z} dicts.
    """
    new_points = []
    for i, point in enumerate(points):
        if isinstance(point, list):
            new_points.append(point)
        elif isinstance(point, dict):
            new_points.append([
                point['x'],
                point['y'],
                point['z']
            ])

    return new_points


@map_paths.route('/locations/<uuid:location_id>/map-paths', methods=['GET'])
async def list_map_paths(location_id):
    """
    List map paths
    ---
    get:
        summary: List map paths
        tags:
         - map-paths
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: mobile_device_id
            in: query
            required: false
            schema:
                type: str
            description: Filter relevant paths for a given mobile device ID (null values are also returned)
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: MapPath
    """
    items = []

    stmt = sa.select(MapPath).where(MapPath.location_id == location_id)

    try:
        mobile_device_id = uuid.UUID(request.args.get("mobile_device_id"))
        stmt = stmt.where(sa.or_(MapPath.mobile_device_id == None, MapPath.mobile_device_id == mobile_device_id))
    except Exception as error:
        pass

    result = await g.session.execute(stmt)
    for row in result.scalars():
        items.append(map_path_schema.dump(row))

    if INFLATE_VECTORS:
        for item in items:
            item['points'] = inflate_vectors(item['points'])

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@map_paths.route('/locations/<uuid:location_id>/map-paths', methods=['POST'])
async def create_map_path(location_id):
    """
    Create map path
    ---
    post:
        summary: Create map path
        description: |-
            Create a new map path, which can be one of many kinds of paths to
            be displayed to the user, e.g. a navigation path, object contour,
            or hand-drawn marking.

            The following example creates a path at a specific point:

                POST /locations/<location_id>/map-paths
                Content-Type: application/json
                {
                    "label": "Directions to exit",
                    "type": "navigation",
                    "color": "#00ff00",
                    "points": [[0, 0, 0], [1, 0, 0], [1, 0, 1]]
                }
        tags:
         - map-paths
        requestBody:
            required: true
            content:
                application/json:
                    schema: MapPath
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: MapPath
    """
    body = await request.get_json()
    body['location_id'] = location_id

    # If client is sending ID, clear it so that it is automatically generated.
    if 'id' in body:
        del body['id']

    if 'points' in body:
        body['points'] = ingest_point_list(body['points'])

    map_path = map_path_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)

    g.session.add(map_path)
    await g.session.commit()

    result = map_path_schema.dump(map_path)

    if INFLATE_VECTORS:
        result['points'] = inflate_vectors(result['points'])

    await current_app.dispatcher.dispatch_event("map-paths:created",
            "/locations/{}/map-paths/{}".format(location_id, map_path.id),
            current=result)

    return jsonify(result), HTTPStatus.CREATED


@map_paths.route('/locations/<uuid:location_id>/map-paths/<int:map_path_id>', methods=['DELETE'])
@auth.requires_admin
async def delete_map_path(location_id, map_path_id):
    """
    Delete map path
    ---
    delete:
        summary: Delete map path
        tags:
         - map-paths
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be deleted
        responses:
            200:
                description: The object which was deleted
                content:
                    application/json:
                        schema: MapPath
    """
    map_path = await g.session.get(MapPath, map_path_id)
    if map_path is None:
        raise exceptions.NotFound(description="Map path {} was not found".format(map_path_id))

    await g.session.delete(map_path)
    await g.session.commit()

    result = map_path_schema.dump(map_path)

    if INFLATE_VECTORS:
        result['points'] = inflate_vectors(result['points'])

    await current_app.dispatcher.dispatch_event("map-paths:deleted",
            "/locations/{}/map-paths/{}".format(location_id, map_path_id),
            previous=result)

    return jsonify(result), HTTPStatus.OK


@map_paths.route('/locations/<uuid:location_id>/map-paths/<int:map_path_id>', methods=['GET'])
async def get_map_path(location_id, map_path_id):
    """
    Get map path
    ---
    get:
        summary: Get map path
        tags:
         - map-paths
        parameters:
          - name: id
            in: path
            required: true
            description: Object ID
        responses:
            200:
                description: The requested object
                content:
                    application/json:
                        schema: MapPath
    """
    map_path = await g.session.get(MapPath, map_path_id)
    if map_path is None:
        raise exceptions.NotFound(description="Map path {} was not found".format(map_path_id))

    result = map_path_schema.dump(map_path)

    if INFLATE_VECTORS:
        result['points'] = inflate_vectors(result['points'])

    return jsonify(result), HTTPStatus.OK


@map_paths.route('/locations/<uuid:location_id>/map-paths', methods=['PUT'])
async def replace_map_path(location_id):
    """
    Replace map path
    ---
    put:
        summary: Replace navigation path
        description: |-
            Create or replace a specific map path. Some of the query
            parameters must be specified to determine which path to replace
            (mobile_device_id, target_marker_id, and/or type). For example,
            this could be used to replace the navigation trail given to a
            specific headset. If the caller knows the map_path_id to update,
            it is recommended to use the PATCH method, instead.

            The following example creates or replaces a navigation path
            for a specific headset.

                PUT /locations/<location_id>/map-paths?mobile_device_id=X&type=navigation
                Content-Type: application/json
                {
                    "label": "Directions for X",
                    "type": "navigation",
                    "color": "#00ff00",
                    "points": [[0, 0, 0], [1, 0, 0], [1, 0, 1]]
                }
        tags:
         - map-paths
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
          - name: mobile_device_id
            in: query
            required: false
            schema:
                type: str
            description: Specific mobile device ID to receive the path
          - name: target_marker_id
            in: query
            required: false
            schema:
                type: int
            description: Target marker ID for the path
          - name: type
            in: query
            required: false
            schema:
                type: str
            description: Type of path (unknown|navigation|object|drawing)
        requestBody:
            required: true
            content:
                application/json:
                    schema: MapPath
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: MapPath
    """
    body = await request.get_json()
    if body is None:
        body = {}
    body['location_id'] = location_id
    if 'id' in body:
        del body['id']
    if 'points' in body:
        body['points'] = ingest_point_list(body['points'])

    stmt = sa.select(MapPath).where(MapPath.location_id == location_id)

    try:
        mobile_device_id = uuid.UUID(request.args.get("mobile_device_id"))
        stmt = stmt.where(MapPath.mobile_device_id == mobile_device_id)
        body['mobile_device_id'] = mobile_device_id
    except:
        pass

    target_marker_id = request.args.get("target_marker_id")
    if target_marker_id is not None:
        stmt = stmt.where(MapPath.target_marker_id == target_marker_id)
        body['target_marker_id'] = int(target_marker_id)

    type = request.args.get("type")
    if type is not None:
        stmt = stmt.where(MapPath.type == type)
        body['type'] = type

    result = await g.session.execute(stmt)

    # This is expected to raise MultipleResultsFound if the query was too ambiguous
    map_path = result.scalar()

    if map_path is None:
        previous = None
        map_path = map_path_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
        map_path.location_id = location_id
        g.session.add(map_path)
        created = True

    else:
        previous = map_path_schema.dump(map_path)
        map_path.update(body)
        created = False
        if INFLATE_VECTORS:
            previous['points'] = inflate_vectors(previous['points'])

    await g.session.commit()

    result = map_path_schema.dump(map_path)
    if INFLATE_VECTORS:
        result['points'] = inflate_vectors(result['points'])

    if created:
        await current_app.dispatcher.dispatch_event("map-paths:created",
                "/locations/{}/map-paths/{}".format(location_id, map_path.id),
                current=result, previous=previous)
        return jsonify(result), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("map-paths:updated",
                "/locations/{}/map-paths/{}".format(location_id, map_path.id),
                current=result, previous=previous)
        return jsonify(result), HTTPStatus.OK


@map_paths.route('/locations/<uuid:location_id>/map-paths/<int:map_path_id>', methods=['PATCH'])
async def update_map_path(location_id, map_path_id):
    """
    Update map path
    ---
    patch:
        summary: Update map path
        description: This method may be used to modify selected fields of the object.
        tags:
         - map-paths
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: MapPath
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: MapPath
    """
    body = await request.get_json()
    if body is None:
        body = {}
    if 'target_marker_id' in body and isinstance(body['target_marker_id'], str):
        body['target_marker_id'] = int(body['target_marker_id'])
    if 'points' in body:
        body['points'] = ingest_point_list(body['points'])

    map_path = await g.session.get(MapPath, map_path_id)
    if map_path is None:
        raise exceptions.NotFound(description="Map Path {} was not found".format(map_path_id))

    previous = map_path_schema.dump(map_path)

    map_path.update(body)
    await g.session.commit()

    result = map_path_schema.dump(map_path)
    if INFLATE_VECTORS:
        previous['points'] = inflate_vectors(previous['points'])
        result['points'] = inflate_vectors(result['points'])

    await current_app.dispatcher.dispatch_event("map-paths:updated",
            "/locations/{}/map-paths/{}".format(location_id, map_path_id),
            current=result, previous=previous)
    return jsonify(result), HTTPStatus.OK
