import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.jsonresource import JsonCollection, JsonResource
from server.resources.geometry import Box


@dataclass
class AnnotationModel(JsonResource):
    """
    Annotation for an image file, e.g. a detected object with its bounding box.
    """
    id:         int

    label:      str = field(default="object")
    boundary:   Box = field(default_factory=Box)
