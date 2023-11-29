import datetime
import uuid

from http import HTTPStatus

import sqlalchemy as sa

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from werkzeug import exceptions

from server.models.streams import Stream
from server.utils.response import maybe_wrap


class StreamSchema(SQLAlchemySchema):
    class Meta:
        model = Stream
        load_instance = True

    id = auto_field(description="Stream ID (UUID)")

    token = auto_field(description="Authentication token for publishing")
    description = auto_field(description="Stream description")

    publisher_addr = auto_field(description="IP address of stream source if active")

    created_time = auto_field(description="Time the stream was created")
    updated_time = auto_field(description="Last time the stream was updated")

    @post_dump(pass_original=True)
    def add_paths(self, data, original, **kwargs):
        # These are not stored in the database but may be useful for clients.
        data['dash_path'] = "/dash/{}/index.mpd".format(original.id)
        data['hls_path'] = "/hls/{}/index.m3u8".format(original.id)
        data['publish_path'] = "/live/{}?token={}".format(original.id, original.token)
        return data


streams = Blueprint('streams', __name__)
stream_schema = StreamSchema()


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

    stream_id = form.get("name", "")
    token = request.args.get("token", "")

    log_stream_event(form)

    stmt = sa.select(Stream) \
            .where(Stream.id == stream_id) \
            .where(Stream.token == token) \
            .limit(1)

    result = await g.session.execute(stmt)
    stream = result.scalar()
    if stream is None:
        raise exceptions.Forbidden(description="Streaming is not permitted")

    stream.publisher_addr = form.get("addr", None)
    stream.updated_time = datetime.datetime.now()
    await g.session.commit()

    return '', HTTPStatus.NO_CONTENT


@streams.route('/streams/on_publish_done', methods=['POST'])
async def on_publish_done():
    """
    Handler for nginx-rtmp on_publish_done, called when a client ends publishing a stream.
    """
    form = await request.form

    log_stream_event(form)

    stream_id = form.get("name", "")

    stmt = sa.select(Stream) \
            .where(Stream.id == stream_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    stream = result.scalar()
    if stream is None:
        return '', HTTPStatus.NO_CONTENT

    stream.publisher_addr = None
    stream.updated_time = datetime.datetime.now()
    await g.session.commit()

    return '', HTTPStatus.NO_CONTENT


@streams.route('/streams', methods=['GET'])
async def list_streams():
    items = []

    stmt = sa.select(Stream)
    result = await g.session.execute(stmt)
    for row in result.scalars():
        items.append(stream_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@streams.route('/streams', methods=['POST'])
async def create_stream():
    body = await request.get_json()
    if body is None:
        body = dict()
    body['id'] = uuid.uuid4()

    stream = stream_schema.load(body, transient=True)

    g.session.add(stream)
    await g.session.commit()

    result = stream_schema.dump(stream)

    return jsonify(result), HTTPStatus.CREATED


@streams.route('/streams/<uuid:stream_id>', methods=['DELETE'])
async def delete_stream(stream_id):
    stmt = sa.select(Stream) \
            .where(Stream.id == stream_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    stream = result.scalar()
    if stream is None:
        raise exceptions.NotFound(description="Stream {} was not found".format(stream_id))

    await g.session.delete(stream)
    await g.session.commit()

    result = stream_schema.dump(stream)

    return jsonif(result), HTTPStatus.OK
