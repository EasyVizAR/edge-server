import os
from http import HTTPStatus
from quart import Blueprint, make_response, jsonify

routes = Blueprint('routes', __name__)

@routes.route('/icon_urls', methods=['GET'])
async def index():
    files = os.listdir('server/frontend/build/icons')
    totalFiles = []
    for file in files:
        totalFiles.append("icons/" + file)

    return await make_response(jsonify({"file_paths": totalFiles}),
                               HTTPStatus.OK)
