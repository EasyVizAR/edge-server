import time

from server.feature.models import FeatureModel
from server.layer.models import LayerModel
from server.scene.models import SceneModel
from server.surface.models import SurfaceModel
from server.resources.dataclasses import dataclass, field
from server.resources.dictresource import DictResource, DictCollection
from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class LocationModel(JsonResource):
    """
    A location such as a building with a definite geographical boundary.

    A location may have one or more features, which are points of interest,
    messages, or other pieces digital information that team members would like
    to share.

    A location may have one or more map layers, e.g. a floor plan for each
    floor of a building.
    """
    id:     str
    name:   str

    model_path: str = field(default=None)
    model_url:  str = field(default=None)

    def on_ready(self):
        self.Feature = JsonCollection(FeatureModel, "feature", parent=self)
        self.Layer = JsonCollection(LayerModel, "layer", parent=self)
        self.Scene = DictCollection(SceneModel, "scenes", id_type="uuid", parent=self)
        self.Surface = JsonCollection(SurfaceModel, "surface", id_type="uuid", parent=self)
