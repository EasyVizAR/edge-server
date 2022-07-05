import time

from server.resources.dataclasses import dataclass, field
from server.resources.jsonresource import JsonCollection, JsonResource
from server.resources.geometry import Box


@dataclass
class LayerModel(JsonResource):
    """
    Graphical representation of a location, generally as a 2D map

    We support three types of layer objects, specificed in the type field.
    generated: a floor plan will be constructed automatically from surface data
    uploaded: an uploaded image
    external: a link to an external image

    For uploaded files, JPEG, PNG, and SVG are supported. We may need to add
    support for PDF uploads and probably convert to an image.

    For external files, we may want to download and store locally at some
    point.  Otherwise, these will not work in the absence of a wide area
    connection.
    """
    id: int

    name:           str = field(default="New Layer")
    type:           str = field(default="generated")
    ready:          bool = field(default=False)
    version:        int = field(default=0,
                                description="Counter that indicates the current image version.")

    contentType:    str = field(default="image/jpeg")
    imagePath:      str = field(default=None)
    imageUrl:       str = field(default=None)
    viewBox:        Box = field(default_factory=Box)

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)
