import asyncio
import datetime
import os
import shutil
import time

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server.location.models import Location
from server.mapping.map_maker import MapMaker
from server.utils.images import ext_from_type, try_send_image, try_send_png
from server.utils.response import maybe_wrap
from server.utils.utils import save_image

from .models import Layer, LayerSchema


layers = Blueprint("layers", __name__)

layer_schema = LayerSchema()


def get_layer_dir(location_id, layer_id):
    return os.path.join(g.data_dir, 'locations', location_id.hex, 'layers', '{:08x}'.format(layer_id))


@layers.route('/locations/<uuid:location_id>/layers', methods=['GET'])
async def list_layers(location_id):
    """
    List layers
    ---
    get:
        summary: List layers
        tags:
         - layers
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
                            items: Layer
    """
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(Layer).where(Layer.location_id == location_id)
        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(layer_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@layers.route('/locations/<uuid:location_id>/layers', methods=['POST'])
async def create_layer(location_id):
    """
    Create layer
    ---
    post:
        summary: Create layer
        tags:
         - layers
        requestBody:
            required: true
            content:
                application/json:
                    schema: Layer
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: Layer
    """
    body = await request.get_json()

    async with g.session_maker() as session:
        stmt = sa.select(Location).where(Location.id == location_id).limit(1)
        result = await session.execute(stmt)
        location = result.scalar()
        if location is None:
            raise exceptions.NotFound(description="Location {} was not found".format(location_id))

        layer = layer_schema.load(body, transient=True)
        layer.location_id = location_id
        session.add(layer)
        await session.commit()

    result = layer_schema.dump(layer)

    return jsonify(result), HTTPStatus.CREATED


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>', methods=['DELETE'])
async def delete_layer(location_id, layer_id):
    """
    Delete layer
    ---
    delete:
        summary: Delete layer
        tags:
         - layers
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
                        schema: Layer
    """
    async with g.session_maker() as session:
        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .where(Layer.id == layer_id)

        result = await session.execute(stmt)
        layer = result.scalar()
        if layer is None:
            raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

        await session.delete(layer)
        await session.commit()

    shutil.rmtree(get_layer_dir(location_id, layer_id), ignore_errors=True)

    result = layer_schema.dump(layer)

    return jsonify(result), HTTPStatus.OK


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>', methods=['GET'])
async def get_layer(location_id, layer_id):
    """
    Get layer
    ---
    get:
        summary: Get layer
        tags:
         - layers
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
                        schema: Layer
    """
    async with g.session_maker() as session:
        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .where(Layer.id == layer_id)
        result = await session.execute(stmt)
        layer = result.scalar()

        # Fix for clients that hard-coded layer ID = 1,
        # find the layer with lowest ID.
        if layer is None and layer_id == 1:
            stmt = sa.select(Layer) \
                    .where(Layer.location_id == location_id) \
                    .order_by(Layer.id) \
                    .limit(1)
            result = await session.execute(stmt)
            layer = result.scalar()

        if layer is None:
            raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    result = layer_schema.dump(layer)

    return jsonify(result), HTTPStatus.OK


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>', methods=['PUT'])
async def replace_layer(location_id, layer_id):
    """
    Replace layer
    ---
    put:
        summary: Replace layer
        tags:
         - layers
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Layer
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Layer
    """
    body = await request.get_json()
    if body is None:
        body = {}
    body['id'] = layer_id
    body['location_id'] = location_id

    async with g.session_maker() as session:
        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .where(Layer.id == layer_id)

        result = await session.execute(stmt)
        layer = result.scalar()

        if layer is None:
            previous = None
            layer = layer_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
            layer.location_id = location_id
            session.add(layer)
            created = True

        else:
            previous = layer_schema.dump(layer)
            layer.update(body)
            layer.updated_time = datetime.datetime.now()
            created = False

        await session.commit()

    result = layer_schema.dump(layer)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK


async def trigger_map_rebuild(location_id):
    # Variables required for the callbacks below:
    loop = asyncio.get_event_loop()
    dispatcher = current_app.dispatcher
    mapping_limiter = current_app.mapping_limiter

    # The pool limiter helps us batch multiple surface updates. If there is
    # already a mapping task pending for this location, then we do not schedule
    # another. This is not a perfect solution, as we may delay or miss
    # processing the last updates.
    if mapping_limiter.try_submit(location_id):
        surface_dir = os.path.join(g.data_dir, 'locations', location_id.hex, 'surfaces')

        map_maker = await MapMaker.build_maker(g.active_incident.id, location_id, surface_dir)
        future = current_app.mapping_pool.submit(map_maker.make_map)

        def map_ready(future):
            mapping_limiter.finished(location_id)

            result = future.result()
            # TODO need to send an event
#            if result.changes > 0:
#                layer = location.Layer.find_by_id(result.layer_id)
#                layer.imagePath = result.image_path
#                layer.ready = True
#                layer.version += 1
#                layer.viewBox = result.view_box
#                layer.save()
#
#                layer_uri = "/locations/{}/layers/{}".format(location.id, layer.id)
#                asyncio.run_coroutine_threadsafe(dispatcher.dispatch_event("layers:updated", layer_uri, current=layer), loop=loop)

        future.add_done_callback(map_ready)


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>', methods=['PATCH'])
async def update_layer(location_id, layer_id):
    """
    Update layer
    ---
    patch:
        summary: Update layer
        description: This method may be used to modify selected fields of the object.
        tags:
         - layers
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Layer
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Layer
    """
    body = await request.get_json()
    if body is None:
        body = {}

    async with g.session_maker() as session:
        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .where(Layer.id == layer_id)

        result = await session.execute(stmt)
        layer = result.scalar()
        if layer is None:
            raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

        layer.update(body)

        # Some clients might be sending 'cutting_height' instead.
        if 'cutting_height' in body:
            layer.reference_height = float(body['cutting_height'])

        layer.updated_time = datetime.datetime.now()
        await session.commit()

    if layer.type == "generated":
        await trigger_map_rebuild(location_id)

    result = layer_schema.dump(layer)

    return jsonify(result), HTTPStatus.OK


async def _get_layer(location_id, layer_id):
    stmt = sa.select(Layer) \
            .where(Layer.location_id == location_id) \
            .where(Layer.id == layer_id)

    result = await g.session.execute(stmt)
    layer = result.scalar()

    # Fix for clients that hard-coded layer ID = 1,
    # find the layer with lowest ID.
    if layer is None and layer_id == 1:
        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .order_by(Layer.id) \
                .limit(1)
        result = await g.session.execute(stmt)
        layer = result.scalar()

    if layer is None:
        raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    return layer


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>/image', methods=['GET'])
async def get_layer_file(location_id, layer_id):
    """
    Get a layer data file
    ---
    get:
        summary: Get a layer image file
        description: |-
            Get the image file associated with a layer. Typically, this will be
            a map image.

            Layers that are automatically generated (type="generated") by the
            server from environment meshes are stored as SVG. The server can
            convert an SVG source to a PNG file if desired. To request a PNG
            file instead, the caller should set the Accept and Width headers.
            Note that while SVG files have no fixed size, when converting to a
            raster format such as PNG, the size of the output image becomes
            very important for visual quality. Refer to the example below.

                GET /locations/03f68b3c-0aa2-42c8-9e1b-077465f66eb9/layers/1/image
                Accept: image/png
                Width: 900
        tags:
          - layers
        parameters:
          - name: Accept
            in: header
            required: false
            schema:
                type: str
            description: |-
                Request a specific content type, e.g. "image/png".

                Not all conversions are supported, and the server will simply
                return an error if the request cannot be satisfied. Converting
                from SVG to PNG is supported, however.
          - name: Width
            in: header
            required: false
            schema:
                type: int
            description: |-
                Request a specific image size (in pixels, default: 900).

                This header value will only be used if a conversion from SVG is performed
                such as when the image is stored as SVG and a PNG is requested.
          - name: features
            in: query
            required: false
            schema:
                type: bool
            description: Overlay icons for features
          - name: headsets
            in: query
            required: false
            schema:
                type: bool
            description: Overlay icons for headsets
        responses:
            200:
                description: The image or other data file.
                content:
                    image/jpeg: {}
                    image/png: {}
                    image/svg+xml: {}
    """
#    if "features" in request.args:
#        # This custom map generation code will overlay markers for the positions of features.
#        map_maker = MapMaker.build_maker(g.active_incident.id, location_id, show_features=True)
#        future = current_app.mapping_pool.submit(map_maker.make_map)
#        result = await asyncio.wrap_future(future)
#        return await try_send_image(result.image_path, layer.contentType, request.headers)
#
#    elif "headsets" in request.args:
#        # This custom map generation code will overlay markers for the positions of headsets.
#        map_maker = MapMaker.build_maker(g.active_incident.id, location_id, show_headsets=True)
#        future = current_app.mapping_pool.submit(map_maker.make_map)
#        result = await asyncio.wrap_future(future)
#        return await try_send_image(result.image_path, layer.contentType, request.headers)
#
#    elif "slices" in request.args:
#        # Experimental mode: caller specifies a list of cutting plane levels,
#        # e.g. "-1,-0.75,-0.5,-0.25,0,0.25,0.5"
#        slices = [float(v) for v in request.args.get("slices").split(",")]
#        map_maker = MapMaker.build_maker(g.active_incident.id, location_id, slices=slices)
#        future = current_app.mapping_pool.submit(map_maker.make_map)
#        result = await asyncio.wrap_future(future)
#        return await try_send_image(result.image_path, layer.contentType, request.headers)

    layer = await _get_layer(location_id, layer_id)

    layer_dir = get_layer_dir(location_id, layer.id)
    layer_fname = "image" + ext_from_type(layer.image_type)
    return await try_send_image(os.path.join(layer_dir, layer_fname), layer.image_type, request.headers)


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>/image.png', methods=['GET'])
async def get_layer_file_png(location_id, layer_id):
    """
    Request layer image as a PNG
    """
    layer = await _get_layer(location_id, layer_id)

    layer_dir = get_layer_dir(location_id, layer_id)
    layer_fname = "image" + ext_from_type(layer.image_type)

    width = request.args.get("width", 900)
    try:
        width = int(width)
    except:
        raise exceptions.BadRequest("Cannot interpret PNG width argument")

    return await try_send_png(os.path.join(layer_dir, layer_fname), layer.image_type, width=width)


@layers.route('/locations/<uuid:location_id>/layers/<int:layer_id>/image', methods=['PUT'])
async def upload_layer_image(location_id, layer_id):
    """
    Upload a layer image
    ---
    put:
        summary: Upload a layer image
        tags:
          - layers
        requestBody:
            required: true
            content:
                image/jpeg: {}
                image/png: {}
                image/svg+xml: {}
    """
    async with g.session_maker() as session:
        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .where(Layer.id == layer_id)

        result = await session.execute(stmt)
        layer = result.scalar()
        if layer is None:
            raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

        layer_dir = get_layer_dir(location_id, layer_id)
        os.makedirs(layer_dir, exist_ok=True)

        temp_filename = "{}-{}".format(location_id.hex, layer_id)
        temp_path = os.path.join(g.temp_dir, temp_filename)

        request_files = await request.files
        if 'image' in request_files:
            await save_image(temp_path, request_files['image'])
        else:
            body = await request.get_data()
            with open(temp_path, "wb") as output:
                output.write(body)

        layer.image_type = current_app.magic.from_file(temp_path)

        if layer.image_type == "image/svg+xml":
            from svgelements import SVG
            vb = SVG.parse(temp_path).viewbox
            layer.boundary_left = vb.x
            layer.boundary_top = vb.y
            layer.boundary_width = vb.width
            layer.boundary_height = vb.height

        final_filename = "image" + ext_from_type(layer.image_type)
        final_path = os.path.join(layer_dir, final_filename)
        shutil.move(temp_path, final_path)

        created = os.path.exists(final_path)

        layer.updated_time = datetime.datetime.now()
        layer.version += 1

        await session.commit()

    result = layer_schema.dump(layer)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK
