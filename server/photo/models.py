import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class PhotoModel(JsonResource):
    id:             int

    contentType:    str = field(default="image/jpeg")
    filePath:       str = field(default=None)
    fileUrl:        str = field(default=None)

    height:         int = field(default=None)
    width:          int = field(default=None)

    retention:      str = field(default="auto")
    status:         str = field(default="created")
    uploadedBy:     str = field(default=None)

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)
