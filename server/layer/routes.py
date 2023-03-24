import asyncio
import os
import time

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.mapping.map_maker import MapMaker
from server.resources.csvresource import CsvCollection
from server.utils.images import try_send_image
from server.utils.utils import save_image

from .models import LayerModel


layers = Blueprint("layers", __name__)


@layers.route('/locations/<location_id>/layers', methods=['GET'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layers = location.Layer.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): layers}
    else:
        result = layers

    return jsonify(result), HTTPStatus.OK


@layers.route('/locations/<location_id>/layers', methods=['POST'])
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

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.load(body, replace_id=True)

    # The layer object should either specify an external fileUrl, or the caller
    # will need to upload a file after creating this object.
    if layer.type == "uploaded":
        if layer.contentType == "image/jpeg":
            extension = "jpeg"
        elif layer.contentType == "image/png":
            extension = "png"
        elif layer.contentType == "image/svg+xml":
            extension = "svg"
        else:
            error = "Unsupported content type ({})".format(layer.contentType)
            raise exceptions.BadRequest(description=error)

        upload_file_name = "image.{}".format(extension)
        layer.imagePath = os.path.join(layer.get_dir(), upload_file_name)
        layer.imageUrl = "/locations/{}/layers/{}/image".format(location_id, layer.id)
        layer.ready = False

    elif layer.type == "generated":
        layer.ready = False

    elif layer.type == "external":
        layer.ready = True

    else:
        error = "Unsupported layer type ({})".format(layer.type)
        raise exceptions.BadyRequest(description=error)

    layer.save()

    return jsonify(layer), HTTPStatus.CREATED


@layers.route('/locations/<location_id>/layers/<layer_id>', methods=['DELETE'])
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

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.find_by_id(layer_id)
    if layer is None:
        raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    layer.delete()

    return jsonify(layer), HTTPStatus.OK


@layers.route('/locations/<location_id>/layers/<layer_id>', methods=['GET'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.find_by_id(layer_id)
    if layer is None:
        raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    return jsonify(layer), HTTPStatus.OK


@layers.route('/locations/<location_id>/layers/<layer_id>', methods=['PUT'])
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
    body['id'] = layer_id

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.load(body)
    created = layer.save()

    if created:
        return jsonify(layer), HTTPStatus.CREATED
    else:
        return jsonify(layer), HTTPStatus.OK


def trigger_map_rebuild(location):
    # Variables required for the callbacks below:
    loop = asyncio.get_event_loop()
    dispatcher = current_app.dispatcher
    mapping_limiter = current_app.mapping_limiter
    Location = g.active_incident.Location

    # The pool limiter helps us batch multiple surface updates. If there is
    # already a mapping task pending for this location, then we do not schedule
    # another. This is not a perfect solution, as we may delay or miss
    # processing the last updates.
    if mapping_limiter.try_submit(location.id):
        map_maker = MapMaker.build_maker(g.active_incident.id, location.id)
        future = current_app.mapping_pool.submit(map_maker.make_map)

        def map_ready(future):
            mapping_limiter.finished(location.id)

            result = future.result()
            if result.changes > 0:
                layer = location.Layer.find_by_id(result.layer_id)
                layer.imagePath = result.image_path
                layer.ready = True
                layer.version += 1
                layer.viewBox = result.view_box
                layer.save()

                layer_uri = "/locations/{}/layers/{}".format(location.id, layer.id)
                asyncio.run_coroutine_threadsafe(dispatcher.dispatch_event("layers:updated", layer_uri, current=layer), loop=loop)

        future.add_done_callback(map_ready)


@layers.route('/locations/<location_id>/layers/<layer_id>', methods=['PATCH'])
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

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.find_by_id(layer_id)
    if layer is None:
        raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    layer.update(body)
    layer.save()

    if layer.type == "generated":
        trigger_map_rebuild(location)

    return jsonify(layer), HTTPStatus.OK


@layers.route('/locations/<location_id>/layers/<layer_id>/image', methods=['GET'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.find_by_id(layer_id)
    if layer is None:
        raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    if "headsets" in request.args:
        # This custom map generation code will overlay markers for the positions of headsets.
        map_maker = MapMaker.build_maker(g.active_incident.id, location_id, show_headsets=True)
        future = current_app.mapping_pool.submit(map_maker.make_map)
        result = await asyncio.wrap_future(future)
        return await try_send_image(result.image_path, layer.contentType, request.headers)

    elif "slices" in request.args:
        # Experimental mode: caller specifies a list of cutting plane levels,
        # e.g. "-1,-0.75,-0.5,-0.25,0,0.25,0.5"
        slices = [float(v) for v in request.args.get("slices").split(",")]
        map_maker = MapMaker.build_maker(g.active_incident.id, location_id, slices=slices)
        future = current_app.mapping_pool.submit(map_maker.make_map)
        result = await asyncio.wrap_future(future)
        return await try_send_image(result.image_path, layer.contentType, request.headers)

    else:
        return await try_send_image(layer.imagePath, layer.contentType, request.headers)


@layers.route('/locations/<location_id>/layers/<layer_id>/image', methods=['PUT'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    layer = location.Layer.find_by_id(layer_id)
    if layer is None:
        raise exceptions.NotFound(description="Layer {} was not found".format(layer_id))

    created = not os.path.exists(layer.imagePath)

    request_files = await request.files
    if 'image' in request_files:
        await save_image(layer.imagePath, request_files['image'])
        if layer.contentType == "image/svg+xml":
            from svgelements import SVG
            vb = SVG.parse(layer.imagePath).viewbox
            layer.viewBox.left = vb.x
            layer.viewBox.top = vb.y
            layer.viewBox.width = vb.width
            layer.viewBox.height = vb.height
    else:
        body = await request.get_data()
        with open(layer.imagePath, "wb") as output:
            output.write(body)

    layer.imageUrl = "/locations/{}/layers/{}/image".format(location_id, layer_id)
    layer.ready = True
    layer.updated = time.time()
    layer.version += 1
    layer.save()

    if created:
        return jsonify(layer), HTTPStatus.CREATED
    else:
        return jsonify(layer), HTTPStatus.OK
