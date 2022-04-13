import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.feature.models import FeatureModel
from server.layer.models import LayerModel
from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class LocationModel(JsonResource):
    id:     str
    name:   str

    def on_ready(self):
        self.Feature = JsonCollection(FeatureModel, "feature", parent=self)
        self.Layer = JsonCollection(LayerModel, "layer", parent=self)
