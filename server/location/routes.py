import asyncio
import datetime
import os
import uuid

from http import HTTPStatus

import pyqrcode

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server import auth
from server.layer.models import Layer
from server.mapping.obj_file import ObjFileMaker
from server.resources.geometry import Vector3f
from server.pose_changes.routes import do_list_check_in_pose_changes
from server.utils.response import maybe_wrap

from .models import DeviceConfiguration, DeviceConfigurationSchema, Location, LocationSchema


locations = Blueprint("locations", __name__)

device_configuration_schema = DeviceConfigurationSchema()
location_schema = LocationSchema()


def get_location_dir(location_id):
    return os.path.join(g.data_dir, 'locations', location_id.hex)


@locations.route('/locations', methods=['GET'])
async def list_locations():
    """
    List locations
    ---
    get:
        summary: List locations
        tags:
         - locations
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
                            items: Location
    """
    items = []

    stmt = sa.select(Location) \
            .options(sa.orm.selectinload(Location.device_configuration))
    result = await g.session.execute(stmt)
    for row in result.scalars():
        items.append(location_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@locations.route('/locations', methods=['POST'])
async def create_location():
    """
    Create location
    ---
    post:
        summary: Create location
        tags:
         - locations
        requestBody:
            required: true
            content:
                application/json:
                    schema: Location
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: Location
    """
    body = await request.get_json()
    body['id'] = uuid.uuid4()

    location = location_schema.load(body, transient=True)

    g.session.add(location)
    await g.session.commit()

    # Create a default configuration set
    location.device_configuration = DeviceConfiguration(location_id=location.id)
    g.session.add(location.device_configuration)
    await g.session.commit()

    result = location_schema.dump(location)

    return jsonify(result), HTTPStatus.CREATED


@locations.route('/locations/<uuid:location_id>', methods=['DELETE'])
@auth.requires_admin
async def delete_location(location_id):
    """
    Delete location
    ---
    delete:
        summary: Delete location
        tags:
         - locations
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
                        schema: Location
    """
    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    await g.session.delete(location)
    await g.session.commit()

    result = location_schema.dump(location)

    return jsonify(result), HTTPStatus.OK


@locations.route('/locations/<uuid:location_id>', methods=['GET'])
async def get_location(location_id):
    """
    Get location
    ---
    get:
        summary: Get location
        tags:
         - locations
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
                        schema: Location
    """
    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .options(sa.orm.selectinload(Location.device_configuration)) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    result = location_schema.dump(location)

    return jsonify(result), HTTPStatus.OK


@locations.route('/locations/<uuid:location_id>', methods=['PUT'])
async def replace_location(location_id):
    """
    Replace location
    ---
    put:
        summary: Replace location
        tags:
         - locations
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Location
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Location
    """
    body = await request.get_json()
    if body is None:
        body = {}
    body['id'] = location_id

    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .options(sa.orm.selectinload(Location.device_configuration)) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()

    if location is None:
        location = location_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
        g.session.add(location)
        created = True

    else:
        location.update(body)
        location.updated_time = datetime.datetime.now()
        created = False

    await g.session.commit()

    result = location_schema.dump(location)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK


@locations.route('/locations/<uuid:location_id>', methods=['PATCH'])
async def update_location(location_id):
    """
    Update location
    ---
    patch:
        summary: Update location
        description: This method may be used to modify selected fields of the object.
        tags:
         - locations
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Location
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Location
    """
    body = await request.get_json()

    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .options(sa.orm.selectinload(Location.device_configuration)) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    location.update(body)
    location.updated_time = datetime.datetime.now()
    await g.session.commit()

    result = location_schema.dump(location)

    return jsonify(result), HTTPStatus.OK


@locations.route('/locations/<uuid:location_id>/device_configuration', methods=['PUT'])
async def replace_location_device_configuration(location_id):
    """
    Replace location device configuration
    ---
    put:
        summary: Replace location device configuration
        tags:
         - locations
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: DeviceConfiguration
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: DeviceConfiguration
    """
    body = await request.get_json()

    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .options(sa.orm.selectinload(Location.device_configuration)) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()

    if location.device_configuration is None:
        config = device_configuration_schema.load(body, transient=True)
        config.location_id = location_id
        config.mobile_device_id = None
        g.session.add(config)
        created = True
        location.device_configuration = config

    else:
        location.device_configuration.update(body)
        location.updated_time = datetime.datetime.now()
        created = False

    await g.session.commit()

    result = device_configuration_schema.dump(location.device_configuration)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK


@locations.route('/locations/<uuid:location_id>/qrcode', methods=['GET'])
async def get_location_qrcode(location_id):
    """
    Get a QR code for the location.
    ---
    get:
        description: Get a QR code for the location.
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
    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    filename = "{}-qrcode.svg".format(location_id.hex)
    path = os.path.join(g.temp_dir, filename)

    url = 'vizar://{}/locations/{}'.format(request.host, location_id)
    code = pyqrcode.create(url, error='L')
    code.svg(path, title=url, scale=16)

    return await send_from_directory(g.temp_dir, filename)


@locations.route('/locations/<uuid:location_id>/model', methods=['GET'])
async def get_location_model(location_id):
    """
    Get a 3D model for the location.
    ---
    get:
        description: Get a 3D model for the location.
        tags:
          - locations
        parameters:
          - name: id
            in: path
            required: true
            description: Location ID
        responses:
            200:
                description: An object model file.
                content:
                    model/obj: {}
    """
    stmt = sa.select(Location) \
            .where(Location.id == location_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    location = result.scalar()
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    location_dir = get_location_dir(location_id)
    obj_path = os.path.join(location_dir, "model.obj")
    if not os.path.exists(obj_path) or os.path.getmtime(obj_path) < location.updated_time.timestamp():
        obj_maker = await ObjFileMaker.build_maker_from_db(location_id)
        future = current_app.modeling_pool.submit(obj_maker.make_obj)
        await asyncio.wrap_future(future)

    return await send_from_directory(location_dir, "model.obj",
            as_attachment=True, attachment_filename="model.obj")


@locations.route('/locations/<uuid:location_id>/route', methods=['GET'])
async def get_location_route(location_id):
    """
    Get a route between two points.
    ---
    get:
        summary: Get a route between two points.
        description: |-
            This method uses the location map to find a path between two
            points.

            The following example queries for a path from coordinate (-2, 0, 7.5) to (22, 0, 9.5).

                GET /locations/224c17c4-dd9a-4d62-a075-61f57438a209/route?from=-2,0,7.5&to=22,0,9.5

            The response will be a list of waypoints that make up a route,
            which might look like the following.

                200 OK
                Content-Type: application/json
                [
                    {"x": -2.0, "y": 0.0, "z": 7.5},
                    {"x": 22.0, "y": 0.0, "z": 9.5}
                ]
        tags:
          - locations
        parameters:
          - name: id
            in: path
            required: true
            description: Location ID
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: from
            in: query
            required: false
            description: Starting point in comma-separated format (x,y,z)
          - name: to
            in: query
            required: false
            description: Ending point in comma-separated format (x,y,z)
        responses:
            200:
                description: A path consisting of a list of points.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Vector3f
    """
    query = request.args

    def get_vector_from_query(name):
        value = query.get(name, "0,0,0")
        return [float(v) for v in value.split(",")]

    try:
        start = get_vector_from_query("from")
        end = get_vector_from_query("to")
    except:
        raise exceptions.BadRequest("Invalid starting or destination point")

    path = current_app.mapper.find_path(location_id, start, end)

    output = []
    for point in path:
        p = dict(zip(("x", "y", "z"), point))
        output.append(p)

    # Wrap the list if the caller requested an envelope.
    if "envelope" in query:
        result = {query.get("envelope"): output}
    else:
        result = output

    return jsonify(result), HTTPStatus.OK
