import time

from typing import Set

from server.resources.dataclasses import dataclass, field
from server.resources.jsonresource import JsonResource, JsonCollection
from server.resources.geometry import Vector3f, Vector4f


@dataclass
class HeadsetModel(JsonResource):
    """
    Headset refers to any individual AR device that participates in the system.

    The most important fields are the name, position, and orientation. It is
    important for all headsets involved in the same activity to synchronize to
    a common coordinate system so that the position and orientation can be
    meaningful.

    The headset object tracks only the most recent position and orientation,
    together known as a "pose". The history of pose changes for a given headset
    is stored separately in the pose-changes resource
    (/headset/{headset_id}/pose-changes).
    """
    id:     str
    name:   str = field(default="New Headset", description="Name of the headset")

    color:  str = field(default="#4477aa",
                        description="Suggested display color for the headset as a seven-character HTML color code.")

    location_id:    str = field(default=None,
                                description="Current location or NULL if unknown or inactive")

    # mapId is deprecated and should be removed after transition to location and layer system
    mapId:  str = field(default=None, description="deprecated")

    position:       Vector3f = field(default_factory=Vector3f,
                                     description="Most recent position relative to current location")
    orientation:    Vector4f = field(default_factory=Vector4f,
                                     description="Most recent orientation relative to current location, represented as a quaternion")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)


# This is the top-level collection of headset data.  Import this and use
# Headset.find(), or other methods to query headsets, create headsets, and so
# on.
Headset = JsonCollection(HeadsetModel, "headset", id_type="uuid")
