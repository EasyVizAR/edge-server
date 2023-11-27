import asyncio
import datetime
import os
import shutil
import time
import uuid

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server.layer.models import LayerSchema
from server.mapping.obj_file import ObjFileMaker
from server.mapping.map_maker import MapMaker
from server.models.layers import Layer
from server.utils.response import maybe_wrap

from .models import Surface, SurfaceSchema


surfaces = Blueprint("surfaces", __name__)

layer_schema = LayerSchema()
surface_schema = SurfaceSchema()

auto_build_obj = False


def get_surface_dir(location_id):
    return os.path.join(g.data_dir, 'locations', location_id.hex, 'surfaces')


@surfaces.route('/locations/<uuid:location_id>/surfaces', methods=['GET'])
async def list_surfaces(location_id):
    """
    List surfaces
    ---
    get:
        summary: List surfaces
        tags:
         - surfaces
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Surface
    """
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(Surface).where(Surface.location_id == location_id)
        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(surface_schema.dump(row))

    await current_app.dispatcher.dispatch_event("features:viewed", "/locations/{}/features".format(str(location_id)))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@surfaces.route('/locations/<uuid:location_id>/surfaces', methods=['DELETE'])
async def clear_surfaces(location_id):
    """
    Clear surfaces
    ---
    delete:
        summary: Clear surfaces
        description: This method deletes ALL surfaces collected in the location.
        tags:
         - surfaces
    """
    async with g.session_maker() as session:
        stmt = sa.delete(Surface).where(Surface.location_id == location_id)
        await session.execute(stmt)
        await session.commit()

    shutil.rmtree(get_surface_dir(location_id), ignore_errors=True)

    return {}, HTTPStatus.OK


@surfaces.route('/locations/<uuid:location_id>/surfaces/<uuid:surface_id>', methods=['DELETE'])
async def delete_surface(location_id, surface_id):
    """
    Delete surface
    ---
    delete:
        summary: Delete surface
        tags:
         - surfaces
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be deleted
        responses:
            200:
                description: The object which was deleted
                content:
                    application/json:
                        schema: Surface
    """
    async with g.session_maker() as session:
        stmt = sa.select(Surface) \
                .where(Surface.location_id == location_id) \
                .where(Surface.id == surface_id)

        result = await session.execute(stmt)
        surface = result.scalar()
        if surface is None:
            raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

        await session.delete(surface)
        await session.commit()

    result = surface_schema.dump(surface)

    return jsonify(result), HTTPStatus.OK


@surfaces.route('/locations/<uuid:location_id>/surfaces/<uuid:surface_id>', methods=['GET'])
async def get_surface(location_id, surface_id):
    """
    Get surface
    ---
    get:
        summary: Get surface
        tags:
         - surfaces
        parameters:
          - name: id
            in: path
            required: true
            description: Object ID
        responses:
            200:
                description: The requested object
                content:
                    application/json:
                        schema: Surface
    """
    async with g.session_maker() as session:
        stmt = sa.select(Surface) \
                .where(Surface.location_id == location_id) \
                .where(Surface.id == surface_id)

        result = await session.execute(stmt)
        surface = result.scalar()
        if surface is None:
            raise exceptions.NotFound(description="Surface {} was not found".format(surface_id))

    result = surface_schema.dump(surface)

    return jsonify(result), HTTPStatus.OK


@surfaces.route('/locations/<uuid:location_id>/surfaces/<uuid:surface_id>', methods=['PUT'])
async def replace_surface(location_id, surface_id):
    """
    Replace surface
    ---
    put:
        summary: Replace surface
        tags:
         - surfaces
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Surface
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Surface

    """
    body = await request.get_json()
    if body is None:
        body = {}
    body['id'] = surface_id
    body['location_id'] = location_id

    async with g.session_maker() as session:
        stmt = sa.select(Surface) \
                .where(Surface.location_id == location_id) \
                .where(Surface.id == surface_id)

        result = await session.execute(stmt)
        surface = result.scalar()

        if surface is None:
            previous = None
            surface = surface_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
            surface.location_id = location_id
            session.add(surface)
            created = True

        else:
            previous = surface_schema.dump(surface)
            surface.update(body)
            surface.updated_time = datetime.datetime.now()
            created = False

        await session.commit()

    result = surface_schema.dump(surface)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK


@surfaces.route('/locations/<uuid:location_id>/surfaces/<uuid:surface_id>/surface.ply', methods=['GET'])
async def get_surface_file(location_id, surface_id):
    """
    Get a surface data file
    ---
    get:
        summary: Get a surface data file
        tags:
          - surfaces
        responses:
            200:
                description: The image or other data file.
                content:
                    application/ply: {}
    """
    surface_fname = "{}.ply".format(surface_id.hex)
    return await send_from_directory(get_surface_dir(location_id), surface_fname)


@surfaces.route('/locations/<uuid:location_id>/surfaces/<surface_id>/surface.ply', methods=['PUT'])
async def upload_surface_file(location_id, surface_id):
    """
    Upload a surface data file
    ---
    put:
        summary: Upload a surface data file
        tags:
          - surfaces
        requestBody:
            required: true
            content:
                application/ply: {}
    """
    try:
        surface_id = uuid.UUID(surface_id)
    except ValueError:
        raise exceptions.BadRequest("Surface ID was not a valid UUID")

    async with g.session_maker() as session:
        stmt = sa.select(Surface) \
                .where(Surface.location_id == location_id) \
                .where(Surface.id == surface_id)

        result = await session.execute(stmt)
        surface = result.scalar()

        if surface is None:
            surface = Surface(id=surface_id, location_id=location_id)
            session.add(surface)
            created = True

        else:
            surface.updated_time = datetime.datetime.now()
            created = False

        await session.commit()

    surface_dir = get_surface_dir(location_id)
    os.makedirs(surface_dir, exist_ok=True)
    fname = "{}.ply".format(surface_id.hex)
    path = os.path.join(surface_dir, fname)

    body = await request.get_data()
    with open(path, "wb") as output:
        output.write(body)

    result = surface_schema.dump(surface)

    event_uri = "/locations/{}/surfaces/{}".format(location_id, surface_id)
    await current_app.dispatcher.dispatch_event("surfaces:updated",
            event_uri, current=result, previous=None)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK
