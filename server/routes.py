import os
from http import HTTPStatus
from quart import Blueprint, current_app, make_response, jsonify

routes = Blueprint('routes', __name__)


@routes.route('/', methods=['GET'])
async def index():
    return await current_app.send_static_file('index.html')


@routes.route('/icon_urls', methods=['GET'])
async def list_icons():
    files = os.listdir('server/frontend/build/icons')
    totalFiles = []
    for file in files:
        totalFiles.append("icons/" + file)

    return await make_response(jsonify({"file_paths": totalFiles}),
                               HTTPStatus.OK)
