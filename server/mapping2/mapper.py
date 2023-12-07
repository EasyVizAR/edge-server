import asyncio
import datetime
import os
import sys
import tempfile
import time
import uuid

from quart import current_app, g

import sqlalchemy as sa

from server.layer.models import Layer, LayerSchema
from server.location.models import Location
from server.mapping.obj_file import ObjFileMaker
from server.models.device_poses import DevicePose
from server.models.surfaces import Surface
from server.models.tracking_sessions import TrackingSession

from .navmesh import NavigationMesh
from .soup import LayerConfig, MeshSoup


layer_schema = LayerSchema()


def get_location_dir(data_dir, location_id):
    return os.path.join(data_dir, "locations", location_id.hex)


def get_layer_dir(data_dir, location_id, layer_id):
    return os.path.join(get_location_dir(data_dir, location_id), "layers", "{:08x}".format(layer_id))


class MappingTask:
    def __init__(self, mesh_dir, cache_dir=None, layer_configs=None, navmesh_path=None, traces=None):
        self.mesh_dir = mesh_dir
        self.navmesh_path = navmesh_path

        self.cache_dir = cache_dir
        self.layer_configs = layer_configs
        self.traces = traces

    def run(self):
        soup = MeshSoup.from_directory(self.mesh_dir, cache_dir=self.cache_dir)
        if self.layer_configs is not None:
            soup.infer_walls(self.layer_configs)

        if self.traces is not None:
            for times, points in self.traces:
                soup.add_trace(times, points)

            if self.navmesh_path is not None:
                navmesh = soup.create_navigation_mesh()
                navmesh.save(self.navmesh_path)

        print("Mapping completed with {} layers and {} traces".format(len(self.layer_configs), len(self.traces)))
        return soup.get_bounding_box()


class Mapper:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir

    def find_path(self, location_id, start, end):
        location_dir = get_location_dir(self.data_dir, location_id)
        navmesh_path = os.path.join(location_dir, "navmesh.pickle")
        if not os.path.exists(navmesh_path):
            return [start, end]

        try:
            navmesh = NavigationMesh.load(navmesh_path)
            path = navmesh.find_path(start, end)
            return path

        except:
            return [start, end]

    async def find_traces(self, location_id):
        traces = []

        stmt = sa.select(TrackingSession) \
                .where(TrackingSession.location_id == location_id)

        result = await g.session.execute(stmt)
        for session in result.scalars():
            stmt = sa.select(DevicePose) \
                    .where(DevicePose.tracking_session_id == session.id) \
                    .order_by(DevicePose.id.asc())

            times = []
            points = []

            result = await g.session.execute(stmt)
            for pose in result.scalars():
                times.append(pose.created_time.timestamp())
                points.append([
                    pose.position_x,
                    pose.position_y,
                    pose.position_z
                ])

            if len(times) > 0:
                traces.append((times, points))

        return traces

    async def start_map_update(self, location_id):
        location = await g.session.get(Location, location_id)

        stmt = sa.select(Layer) \
                .where(Layer.location_id == location_id) \
                .where(Layer.type == "generated")

        result = await g.session.execute(stmt)
        layers = result.scalars().all()

        configs = []
        if len(layers) == 0:
            layer = Layer(location_id=location_id, name="Main", type="generated")
            g.session.add(layer)

            location.updated_time = datetime.datetime.now()

            await g.session.commit()
            layers = [layer]

        for layer in layers:
            output_dir = get_layer_dir(self.data_dir, location_id, layer.id)
            os.makedirs(output_dir, exist_ok=True)
            svg_output = os.path.join(output_dir, 'image.svg')
            config = LayerConfig(height=layer.reference_height, svg_output=svg_output)
            configs.append(config)

        location_dir = get_location_dir(self.data_dir, location_id)
        mesh_dir = os.path.join(location_dir, "surfaces")
        navmesh_path = os.path.join(location_dir, "navmesh.pickle")

        traces = await self.find_traces(location_id)

        cache_dir = os.path.join(g.temp_dir, "chunks", location_id.hex)
        os.makedirs(cache_dir, exist_ok=True)

        return MappingTask(mesh_dir, cache_dir=cache_dir, layer_configs=configs, navmesh_path=navmesh_path, traces=traces)

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
                layer.image_type = "image/svg+xml"
                layer.updated_time = datetime.datetime.now()

                updated_layers.append(layer_schema.dump(layer))

            await session.commit()

        for layer in updated_layers:
            layer_uri = "/locations/{}/layers/{}".format(location_id, layer['id'])
            await dispatcher.dispatch_event("layers:updated", layer_uri, current=layer)

    async def finish_model_build(self, location_id, result, session_maker, dispatcher):
        # placeholder in case we need to write any changes to database,
        # send any notifications to websocket clients, etc.
        pass

    async def on_surface_updated(self, event, uri, *args, **kwargs):
        surface = kwargs['current']

        # URI format:
        # /locations/8371f255-9336-4e26-ada9-067543b00c53/surfaces/bb10c2ae-2d9f-4713-90c4-67dcc30a8308
        parts = uri.split("/")
        location_id = uuid.UUID(parts[2])

        loop = asyncio.get_event_loop()
        mapping_limiter = current_app.mapping_limiter
        modeling_limiter = current_app.modeling_limiter
        dispatcher = current_app.dispatcher
        session_maker = g.session_maker

        if mapping_limiter.try_submit(location_id):
            # This callback fires when the map maker operation finishes.
            # If any changes to the map were made, trigger the async callback above.
            def map_ready(future):
                mapping_limiter.finished(location_id)

                result = future.result()
                asyncio.run_coroutine_threadsafe(self.finish_map_update(location_id, result, session_maker, dispatcher), loop=loop)

            task = await self.start_map_update(location_id)
            future = current_app.mapping_pool.submit(task.run)
            future.add_done_callback(map_ready)

        if modeling_limiter.try_submit(location_id):
            def model_ready(future):
                modeling_limiter.finished(location_id)

                result = future.result()
                asyncio.run_coroutine_threadsafe(self.finish_model_build(location_id, result, session_maker, dispatcher), loop=loop)

            maker = await ObjFileMaker.build_maker_from_db(location_id)
            future = current_app.modeling_pool.submit(maker.make_obj)
            future.add_done_callback(model_ready)


if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <surfaces directory> [cache_dir]".format(sys.argv[0]))
        sys.exit(1)

    if len(sys.argv) >= 3:
        cache_dir = sys.argv[2]
    else:
        cache_dir = None

    soup = MeshSoup.from_directory(sys.argv[1], cache_dir=cache_dir)
