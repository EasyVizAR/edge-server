import asyncio
import os

from http import HTTPStatus
from quart import Blueprint, current_app, g, make_response, jsonify, request, websocket

from . import auth
from .apispec import create_openapi_spec


routes = Blueprint('routes', __name__)


@routes.route('/', methods=['GET'])
@auth.requires_user
async def index():
    return await current_app.send_static_file('index.html')


@routes.route('/openapi.html', methods=['GET'])
async def get_openapi_html():
    return await current_app.send_static_file('openapi.html')


@routes.route('/openapi.json', methods=['GET'])
async def get_openapi_json():
    spec = await create_openapi_spec(current_app, base_url=request.host_url)
    return jsonify(spec.to_dict())


@routes.route('/icon_urls', methods=['GET'])
async def list_icons():
    files = os.listdir('server/frontend/build/icons')
    totalFiles = []
    for file in files:
        totalFiles.append("icons/" + file)

    return await make_response(jsonify({"file_paths": totalFiles}),
                               HTTPStatus.OK)
