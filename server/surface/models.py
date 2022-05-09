import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.jsonresource import JsonCollection, JsonResource
from server.resources.geometry import Box


@dataclass
class SurfaceModel(JsonResource):
    """
    A triangle mesh that can be tracked by a persistent UUID.

    Surfaces are uploaded and stored as PLY files and used by the mapping
    module to produce approximate floor plans for a location.

    Below is an example PLY file which contains a triangle mesh consisting of a
    single triangle.

        ply
        format ascii 1.0
        comment Surface ID: {7696b5c8-272c-46b3-8b9c-98befaa6a9f1}
        element vertex 3
        property double x
        property double y
        property double z
        property double nx
        property double ny
        property double nz
        element face 1
        property list uchar int vertex_index
        end_header
        0.445517 -1.057148 -1.517160 0.000000 0.000000 0.000000
        0.476931 -1.052150 -1.492400 0.000000 0.000000 0.000000
        0.438819 -1.044527 -1.573302 0.000000 0.000000 0.000000
        3 0 1 2
    """
    id: str

    filePath:   str = field(default=None)
    fileUrl:    str = field(default=None)
    uploadedBy: str = field(default=None)

    created:    float = field(default_factory=time.time)
    updated:    float = field(default_factory=time.time)
