import io

import numpy as np

from plyfile import PlyData


def read_ply_file(path):
    try:
        mesh = PlyData.read(path)
    except:
        print("Warning: error parsing PLY file {}".format(path))
        return None

    # Add two attributes for compatibility with existing code.
    mesh.vertices = []
    mesh.normals = []
    for v in mesh['vertex'].data:
        mesh.vertices.append([v['x'], v['y'], v['z']])
        mesh.normals.append([v['nx'], v['ny'], v['nz']])

    try:
        mesh.triangles = np.vstack(mesh['face'].data['vertex_index'])
    except:
        mesh.triangles = []

    # Read PLY file comments for extra key-value pairs that are beyond the PLY
    # file format, e.g. information about the coordinate system in use.
    extra = dict()
    for comment in mesh.comments:
        parts = comment.split(":", 1)
        if len(parts) == 2:
            key = parts[0].lower()
            value = parts[1].strip()
            extra[key] = value
    mesh.extra = extra

    return mesh
