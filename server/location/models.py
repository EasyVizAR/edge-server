
from server.feature.models import FeatureModel
from server.layer.models import LayerModel
from server.scene.models import SceneModel
from server.surface.models import SurfaceModel
from server.resources.dataclasses import dataclass, field
from server.resources.dictresource import DictCollection
from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class HeadsetConfiguration(JsonResource):
    enable_mesh_capture:    bool = field(default=True,
                                         description="Enable automatic capturing of environment surfaces for mapping")
    enable_photo_capture:   bool = field(default=False,
                                         description="Enable automatic capturing of high resolution photos")
    enable_extended_capture:   bool = field(default=False,
                                         description="Enable automatic capturing of photos, depth, geometry, and intensity images")


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

    description: str = field(default=None,
                             description="Location description or notes to be displayed on the dashboard")

    model_path: str = field(default=None)
    model_url:  str = field(default=None)

    last_surface_update: float = field(default=0.0,
                                       description="Last time a surface was updated")

    headset_configuration: HeadsetConfiguration = field(default_factory=HeadsetConfiguration,
                                                        description="Application configuration that headsets receive when checking in")

    def on_ready(self):
        self.Feature = JsonCollection(FeatureModel, "feature", parent=self)
        self.Layer = JsonCollection(LayerModel, "layer", parent=self)
        self.Scene = DictCollection(SceneModel, "scenes", id_type="uuid", parent=self)
        self.Surface = JsonCollection(SurfaceModel, "surface", id_type="uuid", parent=self)
