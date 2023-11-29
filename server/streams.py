from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions


streams = Blueprint('streams', __name__)


def log_stream_event(form):
    print("Stream handler called as {}".format(request.full_path))
    for key, value in form.items():
        print("  {}: {}".format(key, value))


@streams.route('/streams/on_play', methods=['POST'])
async def on_play():
    """
    Handler for nginx-rtmp on_play, called when a client requests to play a stream.
    """
    form = await request.form
    log_stream_event(form)
    return '', HTTPStatus.NO_CONTENT


@streams.route('/streams/on_play_done', methods=['POST'])
async def on_play_done():
    """
    Handler for nginx-rtmp on_play_done, called when a client ends playing a stream.
    """
    form = await request.form
    log_stream_event(form)
    return '', HTTPStatus.NO_CONTENT


@streams.route('/streams/on_publish', methods=['POST'])
async def on_publish():
    """
    Handler for nginx-rtmp on_publish, called when a client requests to publish a stream.
    """
    form = await request.form
    log_stream_event(form)

    # TODO need a more flexible way to authorized stream publishers
    # We just need to keep out troublemakers.
    addr = form.get("addr", "0.0.0.0")
    if addr.startswith("128.105."):
        return '', HTTPStatus.NO_CONTENT
    else:
        raise exceptions.Unauthorized()


@streams.route('/streams/on_publish_done', methods=['POST'])
async def on_publish_done():
    """
    Handler for nginx-rtmp on_publish_done, called when a client ends publishing a stream.
    """
    form = await request.form
    log_stream_event(form)
    return '', HTTPStatus.NO_CONTENT
