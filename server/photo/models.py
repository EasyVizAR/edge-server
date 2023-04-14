import time

from typing import List

from server.resources.dataclasses import dataclass, field
from server.resources.geometry import Box, Vector3f, Vector4f
from server.resources.jsonresource import JsonCollection, JsonResource


ENORMOUS_POSITION_ERROR = 100000.0


@dataclass
class Annotation:
    label:      str = field(default="object")
    confidence: float = field(default=0.0)
    boundary:   Box = field(default_factory=Box)

    position:   Vector3f = field(default=None,
                                 description="Predicted center position of the detected object")
    position_error: float = field(default=ENORMOUS_POSITION_ERROR,
                                    description="Predicted position error (meters)")


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
                                description="Meaning of the data in the file (photo|annotated|depth|geometry|thermal|thumbnail)")

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
    Worker processes such as an object detector may wait for the `ready` flag
    to be set to begin processing.

    The implementation also features an experimental new approach that allows
    an arbitrary number of files to be associated with one photo object. The
    idea is that there may be multiple related images from the same moment in
    time and view point. The primary image is the full resolution color image,
    but we may also have a depth image, a thermal image, a smaller thumbnail
    image, an image with detected objects annotated, and so on. The various
    types of images can be stored and accessed using the "file by name" API
    functions.
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

    retention:      str = field(default="auto",
                                description="Retention policy for the photo (auto|permanent|temporary)")

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

    def infer_missing_annotation_positions(self, inferred_position_error=10.0):
        """
        Update annotations with missing position information.

        This uses the camera position to make a very crude position prediction
        for object locations.
        """
        if self.camera_position is None or self.camera_orientation is None:
            return

        pos = self.camera_position
        rot = self.camera_orientation

        # This math finds the forward vector from the camera_orientation
        # quaternion and adds it to the position vector for the camera. In
        # other words, we predict the object location to be one meter in front
        # of the camera.
        x = pos.x + 2*(rot.x*rot.z + rot.w*rot.y)
        y = pos.y + 2*(rot.y*rot.z - rot.w*rot.x)
        z = pos.z + 1 - 2*(rot.x**2 + rot.y**2)

        for annotation in self.annotations:
            if annotation.position is None or annotation.position_error is None or annotation.position_error > inferred_position_error:
                annotation.position = Vector3f(x, y, z)
                annotation.position_error = inferred_position_error
