import os
import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.resources.csvresource import CsvCollection


surfaces = Blueprint("surfaces", __name__)


@surfaces.route('/surfaces', methods=['GET'])
async def list_surfaces():
    """
    List surfaces
    ---
    get:
        summary: List surfaces
        tags:
         - surfaces
    """
    surfaces = g.active_incident.Surface.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): surfaces}
    else:
        result = surfaces

    return jsonify(result), HTTPStatus.OK



@surfaces.route('/surfaces', methods=['POST'])
async def create_surface():
    """
    Create surface
    ---
    post:
        summary: Create surface
        tags:
         - surfaces
    """
    body = await request.get_json()

    surface = g.active_incident.Surface.load(body, replace_id=True)
    surface.filePath = os.path.join(surface.get_dir(), "surface.ply")
    surface.fileUrl = "/surfaces/{}/surface.ply".format(surface.id)
    surface.save()

    return jsonify(surface), HTTPStatus.CREATED


@surfaces.route('/surfaces/<surface_id>', methods=['DELETE'])
async def delete_surface(surface_id):
    """
    Delete surface
    ---
    delete:
        summary: Delete surface
        tags:
         - surfaces
    """
    surface = g.active_incident.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    surface.delete()

    return jsonify(surface), HTTPStatus.OK


@surfaces.route('/surfaces/<surface_id>', methods=['GET'])
async def get_surface(surface_id):
    """
    Get surface
    ---
    get:
        summary: Get surface
        tags:
         - surfaces
    """
    surface = g.active_incident.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    return jsonify(surface), HTTPStatus.OK


@surfaces.route('/surfaces/<surface_id>', methods=['PUT'])
async def replace_surface(surface_id):
    """
    Replace surface
    ---
    put:
        summary: Replace surface
        tags:
         - surfaces
    """
    body = await request.get_json()
    body['id'] = surface_id

    surface = g.active_incident.Surface.load(body)
    created = surface.save()

    if created:
        return jsonify(surface), HTTPStatus.CREATED
    else:
        return jsonify(surface), HTTPStatus.OK


@surfaces.route('/surfaces/<surface_id>', methods=['PATCH'])
async def update_surface(surface_id):
    """
    Update surface
    ---
    patch:
        summary: Update surface
        tags:
         - surfaces
    """
    surface = g.active_incident.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    surface.update(body)
    surface.save()

    return jsonify(surface), HTTPStatus.OK


@surfaces.route('/surfaces/<surface_id>/surface.ply', methods=['GET'])
async def get_surface_file(surface_id):
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
    surface = g.active_incident.Surface.find_by_id(surface_id)
    if surface is None:
        raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    return await send_from_directory(surface.get_dir(), "surface.ply")


@surfaces.route('/surfaces/<surface_id>/surface.ply', methods=['PUT'])
async def upload_surface_file(surface_id):
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
    surface = g.active_incident.Surface.find_by_id(surface_id)
    if surface is None:
        surface = g.active_incident.Surface(surface_id)
        surface.filePath = os.path.join(surface.get_dir(), "surface.ply")
        surface.fileUrl = "/surfaces/{}/surface.ply".format(surface_id)

    created = not os.path.exists(surface.filePath)

    body = await request.get_data()
    with open(surface.filePath, "wb") as output:
        output.write(body)

    surface.updated = time.time()
    surface.save()

    if created:
        return jsonify(surface), HTTPStatus.CREATED
    else:
        return jsonify(surface), HTTPStatus.OK