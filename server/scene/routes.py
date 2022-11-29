import os
import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions

from server.utils.response import maybe_wrap


scenes = Blueprint('scenes', __name__)

scene_filename = 'scene.json'


@scenes.route('/locations/<location_id>/scenes', methods=['GET'])
async def list_scenes(location_id):
    """
    List scene files available for the location
    ---
    get:
        summary: List scene files available for the location
        tags:
          - scenes
        parameters:
          - name: envelope
            in: query
            required: false
            schema:
                type: str
            description: If set, the returned list will be wrapped in an envelope with this name.
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    scenes = location.Scene.find()

    result = []
    for scene in scenes:
        result.append(scene.id)

    return jsonify(maybe_wrap(result)), HTTPStatus.OK


@scenes.route('/locations/<location_id>/scenes/<headset_id>.json', methods=['GET'])
async def get_scene(location_id, headset_id):
    """
    Get scene JSON file
    ---
    get:
        summary: Get scene JSON file
        tags:
         - scenes
        responses:
            200:
                description: a scene file
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    scene = location.Scene.find_by_id(headset_id)
    if scene is None:
        raise exceptions.NotFound(description="Scene file from headset {} was not found".format(headset_id))

    return await send_from_directory(scene.get_dir(), scene_filename)


@scenes.route('/locations/<location_id>/scenes/<headset_id>.json', methods=['PUT'])
async def replace_scene(location_id, headset_id):
    """
    Replace scene JSON file
    ---
    put:
        summary: Replace scene JSON file
        tags:
         - scenes
        responses:
            204:
                description: Upload successful, no content to return
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    scene = location.Scene.find_by_id(headset_id)
    if scene is None:
        scene = location.Scene.add(headset_id)

    path = os.path.join(scene.get_dir(), scene_filename)

    request_files = await request.files
    if len(request_files) > 0:
        for rfile in request_files.values():
            await rfile.save(path)
            break

    else:
        body = await request.get_data()
        with open(path, "wb") as output:
            output.write(body)

    return jsonify({}), HTTPStatus.NO_CONTENT

