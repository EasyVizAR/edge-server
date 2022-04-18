import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.csvresource import CsvResource
from server.resources.geometry import Vector3f


@dataclass
class PoseChangeModel(CsvResource):
    """
    Record of a headset's position and orientation at a point in time.
    """
    time:           float = field(default_factory=time.time)
    position:       Vector3f = field(default_factory=Vector3f)
    orientation:    Vector3f = field(default_factory=Vector3f)
