import asyncio
import functools
import json
import os
import uuid

import pyqrcode

from http import HTTPStatus
from quart import Blueprint, current_app, request, make_response, jsonify, redirect, send_from_directory
from werkzeug.utils import secure_filename

from server.incidents.incident_handler import init_incidents_handler
from server.mapping.floorplanner import Floorplanner
from server.maps.mapping_thread import MappingThread
from server.maps.maprepository import get_map_repository
from server.utils.utils import get_pixels, GenericJsonEncoder

maps = Blueprint('maps', __name__)

mapping_threads = dict()


example_image_url = "https://pages.cs.wisc.edu/~hartung/easyvizar/seventhfloor.svg"
example_view_box = {
    "left": -35.44230853629791,
    "top": -1.7768587228105028,
    "width": 39.10819374001562,
    "height": 52.83971533602437,
}

map_features_file = "docs/features.json"


def initialize_maps(app):
    """
    Initialize maps storage.

    Make sure the maps directory exists, and create a new "current" map if one
    does not exist. This may make starting up a new system easier.
    """

    maps_repo = get_map_repository()
    maps_dir = maps_repo.get_base_dir()
    os.makedirs(maps_dir, exist_ok=True)


def open_maps_dir():
    """
    Opens the maps directory
    """
    maps_path = get_map_repository().get_base_dir()
    os.makedirs(maps_path, exist_ok=True)
    maps_list = os.listdir(maps_path)
    return maps_list, maps_path


def get_surface_dir(map_id, create=True):
    """
    Returns the directory for map surfaces.
    """
    maps_path = get_map_repository().get_base_dir()
    surface_dir = os.path.join(maps_path, map_id, "surfaces")
    if create:
        os.makedirs(surface_dir, exist_ok=True)
    return surface_dir


def find_map(map_id):
    """
    Finds the map related to the given id
    """

    # opens maps directory
    maps_list, maps_path = open_maps_dir()

    # find map given the id
    for map_dir in maps_list:
        if map_id == map_dir:
            return map_dir, maps_path
            break

    # map not found
    return None, None


def create_map_dir(map_id):
    """
    creates new map directory

    :param map_id:
    :return None if the directory cannot be created, else return the path:
    """
    if not map_id:
        return None

    maps_path = get_map_repository().get_base_dir()
    path = os.path.join(maps_path, map_id)

    try:
        os.mkdir(path)
    except Exception as e:
        return None

    return path


def generate_new_id():
    """
    Creates new map id
    :return: map id
    """

    return uuid.uuid1()


@maps.route('/maps', methods=['GET'])
async def get_all_maps():
    """
    Lists all maps found
    ---
    get:
        description: List maps
        tags:
          - maps
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of Map objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: MapSchema
    """

    # TODO: check authorization
    maps = get_map_repository().get_all_maps()

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): maps}
    else:
        result = maps

    return jsonify(result), HTTPStatus.OK


@maps.route('/maps/<map_id>', methods=['GET'])
async def show_map(map_id):
    """
    Lists the map with the given id
    ---
    get:
        description: Get map
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        responses:
            200:
                description: A Map object
                content:
                    application/json:
                        schema: HeadsetSchema
    """

    # TODO: check authorization

    # check if map exists
    found_map_name, maps_path = find_map(map_id)
    map = get_map_repository().get_map(map_id)
    print(map)
    # check if map exists
    if map is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)
    else:
        return jsonify(map), HTTPStatus.OK


@maps.route('/maps/features', methods=['GET'])
async def list_map_feature_types():
    """
    List map feature types
    ---
    get:
        summary: List map feature types
        description: List all types of map features that the server supports.
            Each map feature type has a name, description, icon for the web view,
            and eventually display information for the AR headset.
        tags:
          - maps
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of map feature type definitions
                content:
                    application/json:
                        schema:
                            type: array
                            items: MapFeatureTypeSchema
    """

    with open(map_features_file, "r") as source:
        features = json.loads(source.read())

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): features}
    else:
        result = features

    return jsonify(result), HTTPStatus.OK


@maps.route('/maps/<map_id>/features', methods=['GET'])
async def list_map_features(map_id):
    """
    Lists the map features with the given id
    ---
    get:
        description: List map features
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of MapFeature objects
                content:
                    application/json:
                        schema:
                            type: array
                            items: MapFeatureSchema
    """

    # TODO: check authorization

    features = get_map_repository().get_map_features(map_id)

    # check if map exists
    if features is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): features}
    else:
        result = features

    return jsonify(result), HTTPStatus.OK


@maps.route('/maps/<map_id>/features', methods=['POST'])
async def add_map_feature(map_id):
    """
    Adds a feature to the map with the given id
    ---
    post:
        description: Add a map feature
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: MapFeatureSchema
        responses:
            201:
                description: MapFeature object
                content:
                    application/json:
                        schema: MapFeatureSchema
    """

    # TODO: check authorization

    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body or 'type' not in body \
            or 'position' not in body or 'style' not in body:
        return await make_response(jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
                                   HTTPStatus.BAD_REQUEST)

    feature_id = None if 'id' not in body else body['id']
    feature = get_map_repository().add_feature(feature_id,
                                               body['name'],
                                               body['type'],
                                               body['mapID'],
                                               body['style'],
                                               position=body['position'])

    # check if map exists
    if feature is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    else:
        return jsonify(feature), HTTPStatus.CREATED


@maps.route('/maps/<map_id>/surfaces', methods=['GET'])
async def list_map_surfaces(map_id):
    """
    Get list of surfaces associated with a map.
    ---
    get:
        description: List surfaces
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        responses:
            200:
                description: A list of surfaces.
                content:
                    application/json:
                        schema:
                            type: array
                            items: SurfaceFileInformationSchema
    """

    # TODO check authorization

    surface_dir = get_surface_dir(map_id, create=False)

    surfaces = []
    for entry in os.scandir(surface_dir):
        if not entry.name.startswith('.') and entry.is_file():
            stat = entry.stat()
            surfaces.append({
                "id": os.path.splitext(entry.name)[0],
                "filename": entry.name,
                "modified": stat.st_mtime,
                "size": stat.st_size
            })

    return jsonify(surfaces), HTTPStatus.OK


@maps.route('/maps/<map_id>/surfaces/<surface_id>', methods=['PUT'])
async def replace_surface(map_id, surface_id):
    """
    Replace a surface.

    This expects to receive a PLY file and stores it in the data directory.
    ---
    put:
        summary: Update map surface
        description: Create or update a surface, which should be a triangle mesh in PLY file format
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        requestBody:
            required: true
            content:
                application/ply: {}
        responses:
            200:
                description: A surface file information object
                content:
                    application/json:
                        schema: SurfaceFileInformationSchema
    """

    # TODO check authorization

    map_repo = get_map_repository()
    map_obj = map_repo.get_map(map_id)
    if map_obj is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    body = await request.get_data()
    if body[0:3].decode() == "ply":
        filename = secure_filename("{}.ply".format(surface_id))
        surface_dir = get_surface_dir(map_id, create=True)
        path = os.path.join(surface_dir, filename)
        is_new = not os.path.exists(path)

        with open(path, "wb") as output:
            output.write(body)

        if map_id not in mapping_threads:
            map_dir = os.path.join(map_repo.get_base_dir(), map_id)
            mapping_threads[map_id] = MappingThread(map_obj, map_dir)
            mapping_threads[map_id].start()

        mapping_threads[map_id].notify()

        stat = os.stat(path)
        surface = {
            "id": surface_id,
            "filename": filename,
            "modified": stat.st_mtime,
            "size": stat.st_size
        }

        if is_new:
            return surface, HTTPStatus.CREATED
        else:
            return surface, HTTPStatus.OK


@maps.route('/maps/<map_id>', methods=['PUT'])
async def replace_map(map_id):
    """
    Replaces a current map
    ---
    put:
        description: Replace a map
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: MapSchema
        responses:
            200:
                description: Map replaced
                content:
                    application/json:
                        schema: MapSchema
            201:
                description: Map created
                content:
                    application/json:
                        schema: MapSchema
    """

    # TODO check authorization

    if not map_id:
        return await make_response(
            jsonify({"message": "No map id",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    # get body of request
    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body or 'image' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    map_name = body['name']
    map_image = body['image']

    id = get_map_repository().replace_map(map_id, map_name, map_image)

    # check if map exists
    if id is None:
        return await make_response(
            jsonify({"message": "The requested map does not exist",
                     "severity": "Warning"}),
            HTTPStatus.NOT_FOUND)

    # map was created
    return await make_response(
        jsonify({"message": "Map replaced",
                 "map_id": id}),
        HTTPStatus.CREATED)


@maps.route('/maps/<map_id>', methods=['DELETE'])
async def delete_map(map_id):
    """
    Delete a map
    ---
    delete:
        description: Delete a map
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        responses:
            200:
                description: Map deleted
    """

    # TODO check authorization

    if not map_id:
        return await make_response(jsonify({"message": "No map id", "severity": "Warning"}), HTTPStatus.BAD_REQUEST)

    deleted = get_map_repository().remove_map(map_id)

    if deleted:

        # map was deleted
        return await make_response(jsonify({"message": "Map deleted"}), HTTPStatus.OK)
    else:

        # map was deleted
        return await make_response(jsonify({"message": "Map could not be deleted"}), HTTPStatus.BAD_REQUEST)


@maps.route('/maps', methods=['POST'])
async def create_map():
    """
    Creates a map
    ---
    post:
        description: Create a map
        tags:
          - maps
        requestBody:
            required: true
            content:
                application/json:
                    schema: MapSchema
        responses:
            201:
                description: Map created
                content:
                    application/json:
                        schema: MapSchema
    """

    # TODO check authorization

    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body or 'image' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    id = None
    if 'id' in body and str(body['id']).strip() != '':
        id = body['id']

    created_id = get_map_repository().add_map(id, body['name'], body['image'])

    return await make_response(
        jsonify({"message": "Map created",
                 "map_id": created_id}),
        HTTPStatus.CREATED)


@maps.route('/image-uploads/', methods=['POST'])
async def image_upload():
    """
    Initiate a file upload
    ---
    post:
        description: Initiate a file upload
        tags:
          - maps
        responses:
            200:
                description: A file upload object
                content:
                    application/json:
                        schema: ImageUploadSchema
    """
    body = await request.get_json()

    if 'intent' not in body or 'data' not in body or 'type' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)
    elif 'maps' == body['intent'] and 'mapID' not in body['data']: # TODO: What is the condition for -> For a feature, it should include bounding box(es) and feature labels.?
        return await make_response(
            jsonify({"message": "Missing parameter in body", "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    return await make_response(jsonify(get_map_repository().create_image(body['intent'], body['data'], body['type'], body['viewBox'])),
                               HTTPStatus.CREATED)


@maps.route('/maps/<map_id>/qrcode', methods=['GET'])
async def get_map_qrcode(map_id):
    """
    Get a QR code for the map.
    ---
    get:
        description: Get a QR code for the map.
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        responses:
            200:
                description: An SVG image file.
                content:
                    image/svg+xml: {}
    """

    # TODO check authorization

    data_dir = current_app.config['VIZAR_DATA_DIR']
    map_dir = os.path.join(data_dir, 'maps', map_id)
    image_path = os.path.join(map_dir, 'qrcode.svg')

    if not os.path.isdir(map_dir):
        return {"error": "Map does not exist."}, HTTPStatus.NOT_FOUND

    if not os.path.exists(image_path):
        url = 'vizar://{}/maps/{}'.format(current_app.config['VIZAR_EDGE_HOST'], map_id)

        code = pyqrcode.create(url, error='L')
        code.svg(image_path, title=url)

    return await send_from_directory(map_dir, 'qrcode.svg')


@maps.route('/maps/<map_id>/top-down.svg', methods=['GET'])
async def get_map_topdown(map_id):
    """
    Get map top-down.svg (deprecated, see /maps/<map_id>/floor-plan.svg).
    """
    location = "/maps/{}/floor-plan.svg".format(map_id)
    return redirect(location)


@maps.route('/maps/<map_id>/floor-plan.svg', methods=['GET'])
async def get_map_floor_plan(map_id):
    """
    Get a floor plan image.
    ---
    get:
        description: Get a floor plan image.
        tags:
          - maps
        parameters:
          - name: id
            in: path
            required: true
            description: Map ID
        responses:
            200:
                description: An SVG image file.
                content:
                    image/svg+xml: {}
    """
    map_dir = os.path.join(get_map_repository().get_base_dir(), map_id)
    image_path = os.path.join(map_dir, 'floor-plan.svg')

    # This should be the common case. The mapping thread runs in the
    # background and produces up-to-date images.
    if os.path.exists(image_path):
        return await send_from_directory(map_dir, 'floor-plan.svg')

    # If the image happens to not exist for some reason, we can do a one-time
    # calculation. This will be a bit slow, unfortunately.
    def create_map():
        ply_files = os.path.join(map_dir, 'surfaces', '*.ply')
        json_file = os.path.join(map_dir, 'floor-plan.json')
        floorplanner = Floorplanner(ply_files, json_data_path=json_file)
        floorplanner.update_lines(initialize=False)
        floorplanner.write_image(image_path)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, create_map)

    return await send_from_directory(map_dir, 'floor-plan.svg')
