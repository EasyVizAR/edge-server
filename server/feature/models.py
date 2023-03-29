import time

from server.resources.dataclasses import dataclass, field
from server.resources.jsonresource import JsonResource
from server.resources.geometry import Vector3f


@dataclass
class FeatureDisplayStyle:
    placement:  str = field(default="point")
    leftOffset: float = field(default=None)
    topOffset:  float = field(default=None)
    radius:     float = field(default=None)


@dataclass
class FeatureModel(JsonResource):
    """
    A map feature such as an important object or location.

    A feature should have a descriptive name, a position in world coordinates,
    and a type, which affects how it is displayed in AR and map overlays.

    Some supported feature types are: fire, warning, injury, door, elevator,
    stairs, user, object, extinguisher, message, headset, ambulance.

    The style field contains additional information for rendering, especially
    in the AR view.

    Placement types:
        "point" - a marker placed at a fixed location
        "floating" - the icon or text should remain in view at a fixed position
                     which is relative to the top-left corner of the AR display
        "surface" - the marker should be rendered on a physical surface such as
                    a wall, at a fixed position relative to the top-left corner
                    of the surface

    Feature types:
        ambulance
        audio
        bad-person
        biohazard
        door
        elevator
        exit
        extinguisher
        fire
        headset
        injury
        message
        object
        person
        photo
        point
        radiation
        stairs
        user
        warning
    """
    id: int

    name:           str = field(default="New Feature",
                                description="Name for the feature")
    color:          str = field(default="#cc6677",
                                description="Suggested display color for the feature as a seven-character HTML color code.")
    position:       Vector3f = field(default_factory=Vector3f,
                                description="Position in world coordinates")
    type:           str = field(default="object",
                                description="Feature type (ambulance|door|elevator|extinguisher|fire|headset|injury|message|object|photo|point|stairs|user|warning)")
    style:          FeatureDisplayStyle = field(default_factory=FeatureDisplayStyle,
                                description="Style information for rendering the feature in AR")

    createdBy:      str = field(default=None,
                                description="User or headset that created the feature")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)
