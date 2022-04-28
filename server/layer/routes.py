import os
import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.resources.csvresource import CsvCollection

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

    return jsonify(layer), HTTPStatus.OK


@layers.route('/locations/<location_id>/layers/<layer_id>/image', methods=['GET'])
async def get_layer_file(location_id, layer_id):
    """
    Get a layer data file
    ---
    get:
        summary: Get a layer data file
        tags:
          - layers
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

    return await send_from_directory(layer.get_dir(), os.path.basename(layer.imagePath))


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
    image = request_files['image']
    from server.utils.utils import save_image
    await save_image(layer.imagePath, image)

    layer.imageUrl = "/locations/{}/layers/{}/image".format(location_id, layer_id)
    layer.ready = True
    layer.updated = time.time()
    layer.save()

    if created:
        return jsonify(layer), HTTPStatus.CREATED
    else:
        return jsonify(layer), HTTPStatus.OK
