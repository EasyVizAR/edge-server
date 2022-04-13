import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.jsonresource import JsonCollection, JsonResource
from server.resources.geometry import Vector3f


@dataclass
class FeatureDisplayStyle:
    placement:  str = field(default="point")
    leftOffset: float = field(default=None)
    topOffset:  float = field(default=None)
    radius:     float = field(default=None)


@dataclass
class FeatureModel(JsonResource):
    id: int

    name:           str = field(default="New Feature")
    position:       Vector3f = field(default_factory=Vector3f)
    type:           str = field(default="object")
    style:          FeatureDisplayStyle = field(default_factory=FeatureDisplayStyle)

    createdBy:      str = field(default=None)

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)
