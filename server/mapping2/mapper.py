import asyncio
import datetime
import os
import uuid

from quart import current_app, g

import sqlalchemy as sa

from server.layer.models import Layer, LayerSchema
from server.location.models import Location

from .mesh_soup import LayerConfig, MeshSoup


layer_schema = LayerSchema()


class MappingTask:
    def __init__(self, mesh_dir, layer_configs=None):
        self.mesh_dir = mesh_dir
        self.layer_configs = layer_configs

    def run(self):
        soup = MeshSoup.from_directory(self.mesh_dir)
        if self.layer_configs is not None:
            soup.infer_walls(self.layer_configs)

        return soup.get_bounding_box()


class Mapper:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir

    async def start_map_update(self, location_id):
        async with g.session_maker() as session:
            location = await session.get(Location, location_id)

            stmt = sa.select(Layer) \
                    .where(Layer.location_id == location_id) \
                    .where(Layer.type == "generated")

            result = await session.execute(stmt)
            layers = result.scalars().all()

            configs = []
            if len(layers) == 0:
                layer = Layer(location_id=location_id, name="Main", type="generated")
                session.add(layer)

                location.updated_time = datetime.datetime.now()

                await session.commit()
                layers = [layer]

            for layer in layers:
                svg_output = os.path.join(self.data_dir, "locations", location_id.hex, "layers", '{:08x}'.format(layer.id), 'image.svg')
                config = LayerConfig(height=layer.reference_height, svg_output=svg_output)
                configs.append(config)

        mesh_dir = os.path.join(self.data_dir, "locations", location_id.hex, "surfaces")

        return MappingTask(mesh_dir, layer_configs=configs)

    async def finish_map_update(self, location_id, result, session_maker, dispatcher):
        updated_layers = []

        async with session_maker() as session:
            stmt = sa.select(Layer) \
                    .where(Layer.location_id == location_id) \
                    .where(Layer.type == "generated")

            res = await session.execute(stmt)
            layers = res.scalars()

            for layer in layers:
                layer.version += 1
                layer.boundary_left = result['left']
                layer.boundary_top = result['top']
                layer.boundary_width = result['width']
                layer.boundary_height = result['height']
                layer.updated_time = datetime.datetime.now()

                updated_layers.append(layer_schema.dump(layer))

            await session.commit()

        for layer in updated_layers:
            layer_uri = "/locations/{}/layers/{}".format(location_id, layer['id'])
            await dispatcher.dispatch_event("layers:updated", layer_uri, current=layer)

    async def on_surface_updated(self, event, uri, *args, **kwargs):
        surface = kwargs['current']

        # URI format:
        # /locations/8371f255-9336-4e26-ada9-067543b00c53/surfaces/bb10c2ae-2d9f-4713-90c4-67dcc30a8308
        parts = uri.split("/")
        location_id = uuid.UUID(parts[2])

        loop = asyncio.get_event_loop()
        mapping_limiter = current_app.mapping_limiter
        dispatcher = current_app.dispatcher
        session_maker = g.session_maker

        if mapping_limiter.try_submit(location_id):
            task = await self.start_map_update(location_id)
            future = current_app.mapping_pool.submit(task.run)

            # This callback fires when the map maker operation finishes.
            # If any changes to the map were made, trigger the async callback above.
            def map_ready(future):
                mapping_limiter.finished(location_id)

                result = future.result()
                asyncio.run_coroutine_threadsafe(self.finish_map_update(location_id, result, session_maker, dispatcher), loop=loop)

            future.add_done_callback(map_ready)
