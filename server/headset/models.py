import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.jsonresource import JsonResource, JsonCollection
from server.resources.geometry import Vector3f


@dataclass
class HeadsetModel(JsonResource):
    id:     str
    name:   str = field(default="New Headset")

    # mapId is deprecated and should be removed after transition to location and layer system
    mapId:  str = field(default=None)

    position:       Vector3f = field(default_factory=Vector3f)
    orientation:    Vector3f = field(default_factory=Vector3f)

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)


# This is the top-level collection of headset data.  Import this and use
# Headset.find(), or other methods to query headsets, create headsets, and so
# on.
Headset = JsonCollection(HeadsetModel, "headset", id_type="uuid")
