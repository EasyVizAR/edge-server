import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.photo.models import PhotoModel
from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class LocationModel(JsonResource):
    id:     str
    name:   str

    def on_ready(self):
#        self.Feature = JsonCollection(FeatureModel, "feature", parent=self)
#        self.Layer = JsonCollection(LayerModel, "layer", parent=self)
        self.Photo = JsonCollection(PhotoModel, "photo", parent=self)
#        self.Surface = JsonCollection(SurfaceModel, "surface", parent=self)
