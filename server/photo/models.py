import time

from typing import List

from server.annotation.models import AnnotationModel
from server.resources.dataclasses import dataclass, field
from server.resources.geometry import Box, Vector3f, Vector4f
from server.resources.jsonresource import JsonCollection, JsonResource


@dataclass
class Annotation:
    label:      str = field(default="object")
    confidence: float = field(default=0.0)
    boundary:   Box = field(default_factory=Box)


@dataclass
class Detector:
    model_repo:     str
    model_name:     str

    torch_version:          str
    torchvision_version:    str
    cuda_enabled:           bool

    preprocess_duration:    float
    inference_duration:     float
    nms_duration:           float


@dataclass
class PhotoFile:
    name:   str

    purpose:        str = field(default="photo",
                                description="Meaning of the data in the file (photo|depth|geometry|thermal|thumbnail)")

    content_type:   str = field(default=None,
                                description="File MIME type (detected during creation)")
    height:         int = field(default=None,
                                description="Photo height in pixels (detected during creation)")
    width:          int = field(default=None,
                                description="Photo width in pixels (detected during creation)")


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
    2. The server responds with a unique URL (imageUrl) for the image.
    3. The headset uploads the image file to the specified location using the
    PUT method.

    The server sets the `ready` flag to true after the image has been uploaded.
    """
    id:             str

    contentType:    str = field(default="image/jpeg",
                                description="File MIME type")
    imagePath:      str = field(default=None,
                                description="Path to file if present on the server")
    imageUrl:       str = field(default=None,
                                description="Either a fully-specified URL (https://...) or a local path on the server (/photos/...)")
    ready:          bool = field(default=False,
                                 description="Indicates imageUrl is valid and ready and presumably readable")
    status:         str = field(default="unknown",
                                description="Status of the image (created|ready|done)")
    priority:       int = field(default=0,
                                description="Priority for image processing, (suggested 1=real-time, 0=normal, -1=background)")

    height:         int = field(default=None)
    width:          int = field(default=None)

    retention:      str = field(default="auto")

    created_by:         str = field(default=None,
                                    description="Headset ID that submitted the photo")
    camera_location_id: str = field(default=None,
                                    description="Location ID where the photo was taken")
    camera_position:    Vector3f = field(default=None,
                                         description="Position of the camera in world coordinates")
    camera_orientation: Vector4f = field(default=None,
                                         description="Orientation of the camera (quaternion)")
    related_feature_id: str = field(default=None,
                                    description="Associated feature ID (if set) for a marker on the map where the photo was taken")

    annotations:    List[Annotation] = field(default_factory=list)
    detector:       Detector = field(default=None,
                                     description="Information about the object detector that was used")

    files:          List[PhotoFile] = field(default_factory=list,
                                            description="List of files associated with this photo")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)

    def on_ready(self):
        self.Annotation = JsonCollection(AnnotationModel, "feature", parent=self)
