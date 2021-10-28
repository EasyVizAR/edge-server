import json
import os
import re

from http import HTTPStatus
from quart import Blueprint, request, make_response, jsonify
from werkzeug.utils import secure_filename


meshes = Blueprint('meshes', __name__)

DEFAULT_ENVIRONMENT_FOLDER = './data'


def get_mesh_dir():
    """
    Opens the meshes directory
    """
    data_dir = os.environ.get("VIZAR_DATA_DIR", DEFAULT_ENVIRONMENT_FOLDER)
    mesh_dir = os.path.join(data_dir, "meshes")
    os.makedirs(mesh_dir, exist_ok=True)
    return mesh_dir


@meshes.route("/meshes/<mesh_id>", methods=["PUT"])
async def update_mesh(mesh_id):
    """
    Update a mesh.

    This expects to receive a PLY file and stores it in the data directory.
    """

    # TODO: check authorization

    body = await request.get_data()
    if body[0:3].decode() == "ply":
        path = os.path.join(get_mesh_dir(), secure_filename("{}.ply".format(mesh_id)))
        is_new = not os.path.exists(path)

        with open(path, "wb") as output:
            output.write(body)

        if is_new:
            return {}, HTTPStatus.CREATED
        else:
            return {}, HTTPStatus.OK
