import time

from dataclasses import field
from typing import List

from marshmallow_dataclass import dataclass

from server.annotation.models import AnnotationModel
from server.resources.geometry import Box
from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class Annotation:
    label:      str = field(default="object")
    boundary:   Box = field(default_factory=Box)


@dataclass
class PhotoModel(JsonResource):
    """
    A photo uploaded by a headset.

    Headsets may upload photos of the environment for various reasons including
    sharing information with other team members or for automatic detection of
    objects in the photo.

    This is easily done with a multi-step procedure:
    1. The headset creates a photo object (POST /photos) with metadata such as
    the file type and image size.
    2. The server responds with a unique URL (fileUrl) for the image.
    3. The headset uploads the image file to the specified location using the
    PUT method.

    The server sets the `ready` flag to true after the image has been uploaded.
    """
    id:             str

    contentType:    str = field(default="image/jpeg")
    filePath:       str = field(default=None)
    fileUrl:        str = field(default=None)
    ready:          bool = field(default=False)

    height:         int = field(default=None)
    width:          int = field(default=None)

    retention:      str = field(default="auto")
    createdBy:      str = field(default=None)

    annotations:    List[Annotation] = field(default_factory=list)

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)

    def on_ready(self):
        self.Annotation = JsonCollection(AnnotationModel, "feature", parent=self)
