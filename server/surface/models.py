import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.jsonresource import JsonCollection, JsonResource
from server.resources.geometry import Box


@dataclass
class SurfaceModel(JsonResource):
    id: str

    locationId: str = field(default=None)

    filePath:   str = field(default=None)
    fileUrl:    str = field(default=None)
    uploadedBy: str = field(default=None)

    created:    float = field(default_factory=time.time)
    updated:    float = field(default_factory=time.time)
