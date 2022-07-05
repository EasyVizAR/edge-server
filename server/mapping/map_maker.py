import collections
import os
import queue
import shutil
import tempfile
import threading
import traceback

from dataclasses import dataclass

from server.incidents.models import Incident
from server.mapping.floorplanner import Floorplanner


@dataclass
class MapMakerResult:
    layer_id: str
    image_path: str
    view_box: dict = None
    changes: int = 0


class MapMaker:
    def __init__(self, layer, surfaces, mapping_state_path, output_path):
        self.layer = layer
        self.surfaces = surfaces
        self.mapping_state_path = mapping_state_path
        self.output_path = output_path

    def make_map(self):
        """
        Rebuild the map for a location from updated surfaces.

        This should be called outside the main thread.
        """
        surface_files = [surface.filePath for surface in self.surfaces]

        floorplanner = Floorplanner(surface_files, json_data_path=self.mapping_state_path)
        changes = floorplanner.update_lines(initialize=False)

        result = MapMakerResult(self.layer.id, self.output_path, changes=changes)
        if changes > 0:
            result.layer_id = self.layer.id
            result.view_box = floorplanner.write_image(self.output_path)
            result.changes = changes
            result.image_path = self.output_path

        return result

    @classmethod
    def build_maker(cls, incident_id, location_id):
        """
        Build a MapMaker instance.

        This should be called from the main thread.
        """
        incident = Incident.find_by_id(incident_id)
        location = incident.Location.find_by_id(location_id)
        surfaces = location.Surface.find()

        layers = location.Layer.find(type="generated")
        if len(layers) == 0:
            layer = location.Layer(id=None, name="Division 0", type="generated", contentType="image/svg+xml")
            layer.contentType = "image/svg+xml"
            layer.imageUrl = "/locations/{}/layers/{}/image".format(location.id, layer.id)
            layer.save()
        else:
            # TODO: different layers for the floors of a building
            layer = layers[0]

        mapping_state_path = os.path.join(layer.get_dir(), "floor_plan.json")
        output_path = os.path.join(layer.get_dir(), "floor_plan.svg")

        return MapMaker(layer, surfaces, mapping_state_path, output_path)
