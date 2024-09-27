import asyncio
import os

from http import HTTPStatus
from quart import Blueprint, current_app, g, make_response, jsonify, redirect, request, websocket
from werkzeug import exceptions

from .connection import WebsocketConnection, WebsocketHandler

from server import auth
from server.utils.response import maybe_wrap


websockets = Blueprint('websockets', __name__)


@websockets.route("/websockets")
async def list_websockets():
    """
    List open websocket connections
    ---
    get:
        summary: List open websocket connections
        tags:
          - websockets
    """
    items = []
    for handler in WebsocketHandler.open_handlers.values():
        items.append(handler.dump())

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@websockets.route("/websockets/<int:websocket_id>", methods=['DELETE'])
@auth.requires_admin
async def delete_websocket(websocket_id):
    """
    Force closed a websocket connection
    ---
    delete:
        summary: Force closed a websocket connection
        tags:
          - websockets
    """
    if websocket_id not in WebsocketHandler.open_handlers:
        raise exceptions.NotFound(description="Websocket {} was not found".format(websocket_id))

    handler = WebsocketHandler.open_handlers[websocket_id]
    await handler.close()

    return jsonify(handler.dump()), HTTPStatus.OK


@websockets.route("/ws", methods=['GET'])
async def get_ws():
    """
    Get the websocket URL

    This route is offered as a convenience for clients to determine
    the URL for opening a websocket connection.

    The answer will be in the response 'Location' header.
    """
    url = "ws://{}/ws".format(request.host)
    return redirect(url, code=300)


@websockets.websocket('/ws')
async def ws():
    """
    Open websocket connection
    ---
    get:
        summary: Open websocket connection
        tags:
          - websockets
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
    if "json-with-header-v2" in websocket.requested_subprotocols:
        chosen_subprotocol = "json-with-header-v2"
    elif "json-with-header" in websocket.requested_subprotocols:
        chosen_subprotocol = "json-with-header"
    elif "json-v2" in websocket.requested_subprotocols:
        chosen_subprotocol = "json-v2"

    conn = WebsocketConnection(websocket)
    handler = WebsocketHandler(current_app.dispatcher, conn,
            subprotocol=chosen_subprotocol, device_id=g.device_id, user_id=g.user_id)
    await asyncio.create_task(handler.listen())
