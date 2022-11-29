import os
import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.location.models import LocationModel
from server.photo.models import PhotoModel
from server.pose_changes.models import PoseChangeModel
from server.surface.models import SurfaceModel

from server.resources.csvresource import CsvCollection
from server.resources.dictresource import DictResource, DictCollection
from server.resources.jsonresource import JsonResource, JsonCollection


@dataclass
class HeadsetContainer(DictResource):
    id: str = field(default=None)

    def on_ready(self):
        self.PoseChange = CsvCollection(PoseChangeModel, "pose-change", parent=self)


@dataclass
class IncidentModel(JsonResource):
    """
    An incident represents an world event with a definite start time.

    It also serves as a container for data created during that event
    such as headset location history, photos, and 3D geometry.
    """
    id:         str = field(default=None)
    name:       str = field(default=None)
    created:    float = field(default_factory=time.time)

    def on_ready(self):
        self.Headset = DictCollection(HeadsetContainer, "headsets", id_type="uuid", parent=self)
        self.Location = JsonCollection(LocationModel, "location", id_type="uuid", parent=self)
        self.Photo = JsonCollection(PhotoModel, "photo", id_type="uuid", parent=self)


Incident = JsonCollection(IncidentModel, "incident", id_type="uuid")
