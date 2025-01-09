import asyncio
import datetime
import os
import sys
import tempfile
import time
import uuid

import sqlalchemy as sa

from server.layer.models import Layer, LayerSchema
from server.location.models import Location
from server.mapping.obj_file import ObjFileMaker
from server.mapping2.scene import LocationModel, MeshColorSource
from server.models.device_poses import DevicePose
from server.models.surfaces import Surface
from server.models.photo_records import PhotoRecord
from server.models.tracking_sessions import TrackingSession
from server.surface.models import SurfaceSchema

from .navmesh import NavigationMesh
from .soup import LayerConfig, MeshSoup


layer_schema = LayerSchema()
surface_schema = SurfaceSchema()

# Use trimesh for OBJ export instead of our custom exporting code.
# Trimesh is faster but does not break out the individual mesh fragments.
use_trimesh_obj_export = True


def get_location_dir(data_dir, location_id):
    return os.path.join(data_dir, "locations", location_id.hex)


def get_layer_dir(data_dir, location_id, layer_id):
    return os.path.join(get_location_dir(data_dir, location_id), "layers", "{:08x}".format(layer_id))


class MappingTaskResult:
    def __init__(self, soup, excluded=None, last_source=None, updated_surfaces=None, unfinished_sources=None):
        self.bounding_box = soup.get_bounding_box()
        self.last_source = last_source

        if excluded is None:
            self.excluded = set()
        else:
            self.excluded = excluded

        if updated_surfaces is None:
            self.updated_surfaces = set()
        else:
            self.updated_surfaces = updated_surfaces

        if unfinished_sources is None:
            self.unfinished_sources = set()
        else:
            self.unfinished_sources = unfinished_sources


class MappingTask:
    def __init__(self, mesh_dir, cache_dir=None, exclude_chunks=set(), layer_configs=None, location_dir=None, navmesh_path=None, color_sources=None, traces=None):
        self.location_dir = location_dir
        self.mesh_dir = mesh_dir
        self.navmesh_path = navmesh_path

        self.cache_dir = cache_dir
        self.exclude_chunks = exclude_chunks
        self.layer_configs = layer_configs
        self.color_sources = color_sources
        self.traces = traces

    def run(self):
        start = time.time()

        scene_file = os.path.join(self.location_dir, "model.pickle")
        model_obj = os.path.join(self.location_dir, "model.obj")

        if os.path.exists(scene_file):
            print("Load scene from {}".format(scene_file))
            scene = LocationModel.from_pickle(scene_file)
            scene.update_from_directory(self.mesh_dir)
        elif os.path.exists(model_obj):
            print("Load scene from {}".format(model_obj))
            scene = LocationModel.from_obj(model_obj)
            scene.update_from_directory(self.mesh_dir)
        else:
            print("Load scene from {}".format(self.mesh_dir))
            scene = LocationModel.from_directory(self.mesh_dir)

        if self.layer_configs is not None:
            scene.infer_walls(self.layer_configs)

        scene.export_obj(model_obj)
        scene.save(scene_file)

#        if self.traces is not None:
#            for times, points in self.traces:
#                soup.add_trace(times, points)
#
#            if self.navmesh_path is not None:
#                navmesh = soup.create_navigation_mesh()
#                navmesh.save(self.navmesh_path)

        duration = time.time() - start
        print("MappingTask completed in {:.3f} seconds".format(duration))
        result = MappingTaskResult(scene)
        return result


class ModelingTask:
    def __init__(self, mesh_dir, cache_dir=None, exclude_chunks=set(), layer_configs=None, location_dir=None, navmesh_path=None, color_sources=None, traces=None):
        self.location_dir = location_dir
        self.mesh_dir = mesh_dir
        self.navmesh_path = navmesh_path

        self.cache_dir = cache_dir
        self.exclude_chunks = exclude_chunks
        self.layer_configs = layer_configs
        self.color_sources = color_sources
        self.traces = traces

        self.max_run_time = 60

    def run(self):
        start = time.time()

        scene_file = os.path.join(self.location_dir, "colored.pickle")
        model_obj = os.path.join(self.location_dir, "model.obj")
        colored_obj = os.path.join(self.location_dir, "colored.obj")
        colored_surfaces_dir = os.path.join(self.location_dir, "colored_surfaces")

        updated_surfaces = set()
        if os.path.exists(scene_file):
            print("Load scene from {}".format(scene_file))
            scene = LocationModel.from_pickle(scene_file)
            updated_surfaces = scene.update_from_directory(self.mesh_dir)
        elif os.path.exists(model_obj):
            print("Load scene from {}".format(model_obj))
            scene = LocationModel.from_obj(model_obj)
            updated_surfaces = scene.update_from_directory(self.mesh_dir)
        else:
            print("Load scene from {}".format(self.mesh_dir))
            scene = LocationModel.from_directory(self.mesh_dir)
            updated_surfaces = set(scene.surface_ids)

        last_source = None
        unfinished_sources = set(self.color_sources)
        if self.color_sources is not None:
            for source in self.color_sources:
                if source not in scene.color_sources:
                    colored_surfaces = scene.apply_color_source(source)
                    updated_surfaces.update(colored_surfaces)
                    last_source = source

                unfinished_sources.remove(source)
                if time.time() - start > self.max_run_time:
                    break

            scene.export_obj(colored_obj, include_color=True)
            scene.save(scene_file)

        os.makedirs(colored_surfaces_dir, exist_ok=True)
        for surface_id in updated_surfaces:
            scene.export_surface_obj(surface_id, colored_surfaces_dir, include_color=True)

        duration = time.time() - start
        print("ModelingTask completed in {:.3f} seconds ending on source {} with {} unfinished".format(duration, last_source, len(unfinished_sources)))
        result = MappingTaskResult(scene, last_source=last_source, updated_surfaces=updated_surfaces, unfinished_sources=unfinished_sources)
        return result


class Mapper:
    def __init__(self, current_app, data_dir="data"):
        self.data_dir = data_dir
        self.exclude_chunks = set()

        self.current_app = current_app

    def find_path(self, location_id, start, end):
        location_dir = get_location_dir(self.data_dir, location_id)
        navmesh_path = os.path.join(location_dir, "navmesh.pickle")
        if not os.path.exists(navmesh_path):
            return [start, end]

        try:
            navmesh = NavigationMesh.load(navmesh_path)
            path = navmesh.find_path(start, end)
            return path.tolist()

        except:
            return [start, end]

    async def find_photos(self, location_id, last_color_source_id=None):
        sources = []

        if last_color_source_id is None:
            last_color_source_id = -1

        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.location_id == location_id) \
                .where(PhotoRecord.id > last_color_source_id) \
                .options(sa.orm.selectinload(PhotoRecord.camera)) \
                .options(sa.orm.selectinload(PhotoRecord.files)) \
                .options(sa.orm.selectinload(PhotoRecord.pose)) \
                .order_by(PhotoRecord.id.asc())

        async with self.current_app.session_maker() as session:
            result = await session.execute(stmt)
            for photo in result.scalars():
                for file in photo.files:
                    if file.purpose == "photo":
                        path = os.path.join(self.data_dir, "locations", location_id.hex, "photos", "{:08x}".format(photo.id), file.name)
                        focal = photo.camera.get_relative_focal_lengths()
                        position = photo.pose.position.as_array()
                        rotation = photo.pose.orientation.as_rotation_matrix()
                        sources.append(MeshColorSource(photo.id, path, focal, position, rotation))

        return sources

    async def start_map_update(self, location_id):
        async with self.current_app.session_maker() as session:
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
            output_dir = get_layer_dir(self.data_dir, location_id, layer.id)
            os.makedirs(output_dir, exist_ok=True)
            svg_output = os.path.join(output_dir, 'image.svg')
            config = LayerConfig(height=layer.reference_height, svg_output=svg_output)
            configs.append(config)

        location_dir = get_location_dir(self.data_dir, location_id)
        mesh_dir = os.path.join(location_dir, "surfaces")
        navmesh_path = os.path.join(location_dir, "navmesh.pickle")

        #traces = await self.find_traces(location_id)

        cache_dir = os.path.join(self.current_app.temp_dir, "locations", location_id.hex)
        os.makedirs(cache_dir, exist_ok=True)

        return MappingTask(mesh_dir, cache_dir=cache_dir,
                exclude_chunks=self.exclude_chunks, layer_configs=configs,
                location_dir=location_dir, navmesh_path=navmesh_path)

    async def finish_map_update(self, location_id, result):
        updated_layers = []

        # Update our set of surface IDs to be excluded from future tasks.
        # These are surfaces which are made redundant by newer surfaces.
        self.exclude_chunks.update(result.excluded)

        async with self.current_app.session_maker() as session:
            stmt = sa.select(Layer) \
                    .where(Layer.location_id == location_id) \
                    .where(Layer.type == "generated")

            res = await session.execute(stmt)
            layers = res.scalars()

            for layer in layers:
                layer.version += 1
                layer.boundary_left = result.bounding_box['left']
                layer.boundary_top = result.bounding_box['top']
                layer.boundary_width = result.bounding_box['width']
                layer.boundary_height = result.bounding_box['height']
                layer.image_type = "image/svg+xml"
                layer.updated_time = datetime.datetime.now()

                updated_layers.append(layer_schema.dump(layer))

            await session.commit()

        for layer in updated_layers:
            layer_uri = "/locations/{}/layers/{}".format(location_id, layer['id'])
            await self.current_app.dispatcher.dispatch_event("layers:updated", layer_uri, current=layer)

    async def start_model_update(self, location_id):
        async with self.current_app.session_maker() as session:
            location = await session.get(Location, location_id)

            location_dir = get_location_dir(self.data_dir, location_id)
            mesh_dir = os.path.join(location_dir, "surfaces")

            photos = await self.find_photos(location_id, location.last_color_source_id)
            print("Found {} photos".format(len(photos)))
            print(photos[0])

            cache_dir = os.path.join(self.current_app.temp_dir, "locations", location_id.hex)
            os.makedirs(cache_dir, exist_ok=True)

        return ModelingTask(mesh_dir, cache_dir=cache_dir,
                location_dir=location_dir, color_sources=photos)

    async def finish_model_update(self, location_id, result):
        async with self.current_app.session_maker() as session:
            location = await session.get(Location, location_id)
            if result.last_source is not None:
                location.last_color_source_id = result.last_source.id
            location.model_version += 1
            await session.commit()

    async def try_start_map_update(self, location_id):
        loop = asyncio.get_event_loop()

        # The mapping process will create the uncolored mesh and 2D floor plan images.
        if self.current_app.mapping_limiter.try_submit(location_id):
            # This callback fires when the map maker operation finishes.
            # If any changes to the map were made, trigger the async callback above.
            def map_ready(future):
                self.current_app.mapping_limiter.finished(location_id)

                result = future.result()
                asyncio.run_coroutine_threadsafe(self.finish_map_update(location_id, result), loop=loop)

                asyncio.run_coroutine_threadsafe(self.try_start_model_update(location_id), loop=loop)

            task = await self.start_map_update(location_id)
            future = self.current_app.mapping_pool.submit(task.run)
            future.add_done_callback(map_ready)

    async def try_start_model_update(self, location_id):
        loop = asyncio.get_event_loop()

        # The modeling process will create the colored mesh.
        # There is some redundancy between the mapping and modeling processes, but
        # the color projection is so slow, it makes sense to run them separately for now.
        if self.current_app.modeling_limiter.try_submit(location_id):
            def model_ready(future):
                self.current_app.modeling_limiter.finished(location_id)

                result = future.result()
                asyncio.run_coroutine_threadsafe(self.finish_model_update(location_id, result), loop=loop)

                # Keep restarting the modeling task until we have finished going through the backlog
                if len(result.unfinished_sources) > 0:
                    asyncio.run_coroutine_threadsafe(self.try_start_model_update(location_id), loop=loop)

            task = await self.start_model_update(location_id)
            future = self.current_app.modeling_pool.submit(task.run)
            future.add_done_callback(model_ready)

    async def on_surface_updated(self, event, uri, *args, **kwargs):
        surface = kwargs['current']

        # URI format:
        # /locations/8371f255-9336-4e26-ada9-067543b00c53/surfaces/bb10c2ae-2d9f-4713-90c4-67dcc30a8308
        parts = uri.split("/")
        location_id = uuid.UUID(parts[2])

        # Process control flow
        #
        # Main                  Mapping         Modeling
        # ----------------------------------------------
        # start_map_update
        #                       MappingTask.run
        # finish_map_update
        # start_model_update
        #                                       ModelingTask.run
        # finish_model_update
        # start_model_update
        #                                       ModelingTask.run
        # finish_model_update
        # ...
        await self.try_start_map_update(location_id)


if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <surfaces directory> [cache_dir]".format(sys.argv[0]))
        sys.exit(1)

    if len(sys.argv) >= 3:
        cache_dir = sys.argv[2]
    else:
        cache_dir = None

    soup = MeshSoup.from_directory(sys.argv[1], cache_dir=cache_dir)
