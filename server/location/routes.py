import asyncio
import os

from http import HTTPStatus

import pyqrcode

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.incidents.models import Incident
from server.mapping.obj_file import ObjFileMaker
from server.resources.csvresource import CsvCollection

from .models import LocationModel


locations = Blueprint("locations", __name__)


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

    locations = g.active_incident.Location.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): locations}
    else:
        result = locations

    return jsonify(result), HTTPStatus.OK


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

    location = g.active_incident.Location.load(body, replace_id=True)
    location.save()

    return jsonify(location), HTTPStatus.CREATED


@locations.route('/locations/<location_id>', methods=['DELETE'])
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

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    location.delete()

    return jsonify(location), HTTPStatus.OK


@locations.route('/locations/<location_id>', methods=['GET'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    return jsonify(location), HTTPStatus.OK


@locations.route('/locations/<location_id>', methods=['PUT'])
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
    body['id'] = location_id

    location = g.active_incident.Location.load(body)
    created = location.save()

    if created:
        return jsonify(location), HTTPStatus.CREATED
    else:
        return jsonify(location), HTTPStatus.OK


@locations.route('/locations/<location_id>', methods=['PATCH'])
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

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    location.update(body)
    location.save()

    return jsonify(location), HTTPStatus.OK


@locations.route('/locations/<location_id>/qrcode', methods=['GET'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    image_path = os.path.join(location.get_dir(), "qrcode.svg")
    if not os.path.exists(image_path):
        url = 'vizar://{}/locations/{}'.format(request.host, location_id)
        code = pyqrcode.create(url, error='L')
        code.svg(image_path, title=url, scale=16)

    return await send_from_directory(location.get_dir(), "qrcode.svg")


@locations.route('/locations/<location_id>/model', methods=['GET'])
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
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    obj_path = os.path.join(location.get_dir(), "model.obj")

    surfaces = location.Surface.find()
    obj_maker = ObjFileMaker(surfaces)
    future = current_app.mapping_pool.submit(obj_maker.make_obj, obj_path)
    await asyncio.wrap_future(future)

    return await send_from_directory(location.get_dir(), "model.obj")
