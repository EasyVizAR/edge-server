import asyncio
import os

from http import HTTPStatus
from quart import Blueprint, current_app, make_response, jsonify, websocket

from .apispec import create_openapi_spec
from .websocket import WebsocketHandler


routes = Blueprint('routes', __name__)


@routes.route('/', methods=['GET'])
async def index():
    return await current_app.send_static_file('index.html')


@routes.route('/openapi.html', methods=['GET'])
async def get_openapi_html():
    return await current_app.send_static_file('openapi.html')


@routes.route('/openapi.json', methods=['GET'])
async def get_openapi_json():
    spec = await create_openapi_spec(current_app)
    return jsonify(spec.to_dict())


@routes.route('/icon_urls', methods=['GET'])
async def list_icons():
    files = os.listdir('server/frontend/build/icons')
    totalFiles = []
    for file in files:
        totalFiles.append("icons/" + file)

    return await make_response(jsonify({"file_paths": totalFiles}),
                               HTTPStatus.OK)


@routes.websocket('/ws')
async def ws():
    """
    Open websocket connection
    ---
    get:
        summary: Open websocket connection
        description: |-
            Commands:
            - subscribe (resource:event) [uri filter]

                Subscribe to event notifications of a certain type specified by
                an event string and optional URI filter.

                The event type is a string that specifies the resource type and
                event outcome separated by a colon, e.g. "headsets:created"
                occurs when a headset is created.

                Supported resource types: headsets, features
                Supported event outcomes: created, deleted, updated, viewed

                The URI filter can be used to limit the event notifications
                to specific subcollections or individual items. The wildcard
                character (*) can be used throughout the URI.

                Examples:

                    subscribe headsets:created
                    subscribe headsets:updated /headsets/*
                    subscribe features:created /locations/*/features
                    subscribe features:updated /locations/123/features

            - unsubscribe <event> [uri filter]

                Unsubscribe from event notifications of a certain type following
                the same syntax as the subscribe event.
    """
    chosen_subprotocol = "json"
    if "json-with-header" in websocket.requested_subprotocols:
        chosen_subprotocol = "json-with-header"

    handler = WebsocketHandler(current_app.dispatcher, websocket.receive,
            websocket.send, subprotocol=chosen_subprotocol)
    await asyncio.create_task(handler.listen())
