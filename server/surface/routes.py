import asyncio
import datetime
import os
import shutil
import time

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server.mapping.obj_file import ObjFileMaker
from server.mapping.map_maker import MapMaker
from server.utils.response import maybe_wrap

from .models import Surface, SurfaceSchema


surfaces = Blueprint("surfaces", __name__)

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


@surfaces.route('/locations/<uuid:location_id>/surfaces/<uuid:surface_id>/surface.ply', methods=['PUT'])
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

    # Variables required for the callbacks below:
    loop = asyncio.get_event_loop()
    dispatcher = current_app.dispatcher
    mapping_limiter = current_app.mapping_limiter
    modeling_limiter = current_app.modeling_limiter

    # The pool limiter helps us batch multiple surface updates. If there is
    # already a mapping task pending for this location, then we do not schedule
    # another. This is not a perfect solution, as we may delay or miss
    # processing the last updates.
    if mapping_limiter.try_submit(location_id):
        map_maker = await MapMaker.build_maker(g.active_incident.id, location_id, get_surface_dir(location_id))
        future = current_app.mapping_pool.submit(map_maker.make_map)

        def map_ready(future):
            mapping_limiter.finished(location_id)

            result = future.result()

            # TODO: Need to update layer and send an event

#            if result.changes > 0:
#                layer = location.Layer.find_by_id(result.layer_id)
#                layer.imagePath = result.image_path
#                layer.ready = True
#                layer.version += 1
#                layer.viewBox = result.view_box
#                layer.save()
#
#                layer_uri = "/locations/{}/layers/{}".format(location_id, layer.id)
#                asyncio.run_coroutine_threadsafe(dispatcher.dispatch_event("layers:updated", layer_uri, current=layer), loop=loop)

        future.add_done_callback(map_ready)

    # auto_build_obj flag enables or disables rebuilding the model obj file
    # This is quite a bit of extra computation for an infrequently used file.
    # It is probably better to lazily update the model file when requested.
    if auto_build_obj and modeling_limiter.try_submit(location_id):
        obj_maker = ObjFileMaker.build_maker(g.active_incident.id, location_id)
        future = current_app.modeling_pool.submit(obj_maker.make_obj)

        def model_ready(future):
            modeling_limiter.finished(location_id)

            result = future.result()

            # TODO: Need to update location and send an event

#            location = Location.find_by_id(location_id)
#            location.model_path = obj_maker.output_path
#            location.model_url = "/locations/{}/model".format(location_id)
#            location.save()
#
#            location_uri = "/locations/{}".format(location_id)
#            asyncio.run_coroutine_threadsafe(dispatcher.dispatch_event("locations:updated", location_uri, current=location), loop=loop)

        future.add_done_callback(model_ready)

    result = surface_schema.dump(surface)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK
