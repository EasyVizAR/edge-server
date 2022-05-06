import os
import time

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.resources.csvresource import CsvCollection


surfaces = Blueprint("surfaces", __name__)


@surfaces.route('/locations/<location_id>/surfaces', methods=['GET'])
async def list_surfaces(location_id):
    """
    List surfaces
    ---
    get:
        summary: List surfaces
        tags:
         - surfaces
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
                            items: Surface
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surfaces = location.Surface.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): surfaces}
    else:
        result = surfaces

    return jsonify(result), HTTPStatus.OK


@surfaces.route('/locations/<location_id>/surfaces', methods=['POST'])
async def create_surface(location_id):
    """
    Create surface
    ---
    post:
        summary: Create surface
        tags:
         - surfaces
        requestBody:
            required: true
            content:
                application/json:
                    schema: Surface
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: Surface
    """
    body = await request.get_json()

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.load(body, replace_id=True)
    surface.filePath = os.path.join(surface.get_dir(), "surface.ply")
    surface.fileUrl = "/locations/{}/surfaces/{}/surface.ply".format(location.id, surface.id)
    surface.save()

    return jsonify(surface), HTTPStatus.CREATED


@surfaces.route('/locations/<location_id>/surfaces/<surface_id>', methods=['DELETE'])
async def delete_surface(location_id, surface_id):
    """
    Delete surface
    ---
    delete:
        summary: Delete surface
        tags:
         - surfaces
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
                        schema: Surface
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    surface.delete()

    return jsonify(surface), HTTPStatus.OK


@surfaces.route('/locations/<location_id>/surfaces/<surface_id>', methods=['GET'])
async def get_surface(location_id, surface_id):
    """
    Get surface
    ---
    get:
        summary: Get surface
        tags:
         - surfaces
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
                        schema: Surface
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    return jsonify(surface), HTTPStatus.OK


@surfaces.route('/locations/<location_id>/surfaces/<surface_id>', methods=['PUT'])
async def replace_surface(location_id, surface_id):
    """
    Replace surface
    ---
    put:
        summary: Replace surface
        tags:
         - surfaces
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Surface
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Surface

    """
    body = await request.get_json()
    body['id'] = surface_id

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.load(body)
    created = surface.save()

    if created:
        return jsonify(surface), HTTPStatus.CREATED
    else:
        return jsonify(surface), HTTPStatus.OK


@surfaces.route('/locations/<location_id>/surfaces/<surface_id>', methods=['PATCH'])
async def update_surface(location_id, surface_id):
    """
    Update surface
    ---
    patch:
        summary: Update surface
        description: This method may be used to modify selected fields of the object.
        tags:
         - surfaces
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Surface
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Surface
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    surface.update(body)
    surface.save()

    return jsonify(surface), HTTPStatus.OK


@surfaces.route('/locations/<location_id>/surfaces/<surface_id>/surface.ply', methods=['GET'])
async def get_surface_file(location_id, surface_id):
    """
    Get a surface data file
    ---
    get:
        summary: Get a surface data file
        tags:
          - surfaces
        responses:
            200:
                description: The image or other data file.
                content:
                    application/ply: {}
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    return await send_from_directory(surface.get_dir(), "surface.ply")


@surfaces.route('/locations/<location_id>/surfaces/<surface_id>/surface.ply', methods=['PUT'])
async def upload_surface_file(location_id, surface_id):
    """
    Upload a surface data file
    ---
    put:
        summary: Upload a surface data file
        tags:
          - surfaces
        requestBody:
            required: true
            content:
                application/ply: {}
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    surface = location.Surface.find_by_id(surface_id)
    if surface is None:
        surface = location.Surface(surface_id)
        surface.filePath = os.path.join(surface.get_dir(), "surface.ply")
        surface.fileUrl = "/locations/{}/surfaces/{}/surface.ply".format(location.id, surface.id)
        surface.save()

    created = not os.path.exists(surface.filePath)

    body = await request.get_data()
    with open(surface.filePath, "wb") as output:
        output.write(body)

    surface.updated = time.time()
    surface.save()

    current_app.mapping_thread.enqueue_task(g.active_incident.id, location_id)

    if created:
        return jsonify(surface), HTTPStatus.CREATED
    else:
        return jsonify(surface), HTTPStatus.OK
