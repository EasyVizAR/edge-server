import datetime
import os

from dataclasses import dataclass

from quart import current_app, g

import marshmallow
import sqlalchemy as sa

from server.layer.models import Layer
from server.location.models import Location
from server.mapping.floorplanner import Floorplanner
from server.surface.models import Surface


@dataclass
class MapMakerResult:
    layer_id: str
    image_path: str
    view_box: dict = None
    changes: int = 0


class MapMaker:
    def __init__(self, layer_id, surfaces, mapping_state_path, output_path, cutting_height=0.0, features=None, headsets=None, slices=None):
        self.layer_id = layer_id
        self.surfaces = surfaces
        self.mapping_state_path = mapping_state_path
        self.output_path = output_path
        self.cutting_height = cutting_height
        self.features = features
        self.headsets = headsets
        self.slices = slices

    def make_map(self):
        """
        Rebuild the map for a location from updated surfaces.

        This should be called outside the main thread.
        """
        #surface_files = [surface.filePath for surface in self.surfaces]
        surface_files = self.surfaces

        floorplanner = Floorplanner(surface_files,
                json_data_path=self.mapping_state_path,
                cutting_height=self.cutting_height,
                features=self.features,
                headsets=self.headsets,
                slices=self.slices)
        changes = floorplanner.update_lines(initialize=False)

        result = MapMakerResult(self.layer_id, self.output_path, changes=changes)
        if changes > 0 or self.features is not None or self.headsets is not None or self.slices is not None:
            result.layer_id = self.layer_id
            result.view_box = floorplanner.write_image(self.output_path)
            result.changes = changes
            result.image_path = self.output_path

            # Create a grid from wall segments for the navigation code to use.
            npz_path = os.path.join(os.path.dirname(self.mapping_state_path), "walls.npz")
            floorplanner.write_grid(result.view_box, npz_path)

        return result

    @classmethod
    async def build_maker(cls, incident_id, location_id, surface_dir, show_features=False, show_headsets=False, slices=None):
        """
        Build a MapMaker instance.

        This should be called from the main thread.
        """
        async with g.session_maker() as session:
            location = await session.get(Location, location_id)

            stmt = sa.select(Layer) \
                    .where(Layer.location_id == location_id) \
                    .where(Layer.type == "generated")

            result = await session.execute(stmt)
            layers = result.scalars().all()

            if len(layers) == 0:
                layer = Layer(location_id=location_id, name="Division 0", type="generated")
                session.add(layer)

                location.updated_time = datetime.datetime.now()

                await session.commit()

            else:
                # TODO: different layers for the floors of a building
                layer = layers[0]

#        if show_features:
#            output_path = os.path.join(layer.get_dir(), "floor_plan_features.svg")
#            features = location.Feature.find()
#        elif show_headsets:
#            output_path = os.path.join(layer.get_dir(), "floor_plan_headsets.svg")
#            headsets = Headset.find(location_id=location_id)
#        elif slices is not None:
#            output_path = os.path.join(layer.get_dir(), "floor_plan_slices.svg")
#        else:
#            output_path = os.path.join(layer.get_dir(), "floor_plan.svg")

        surfaces = []
        if os.path.exists(surface_dir):
            for fname in os.listdir(surface_dir):
                surfaces.append(os.path.join(surface_dir, fname))

        layer_dir = os.path.join(g.data_dir, 'locations', location_id.hex, 'layers', '{:08x}'.format(layer.id))
        mapping_state_path = os.path.join(layer_dir, "floor_plan.json")
        output_path = os.path.join(layer_dir, "image.svg")

        return MapMaker(layer.id, surfaces, mapping_state_path, output_path,
                cutting_height=float(layer.reference_height))
