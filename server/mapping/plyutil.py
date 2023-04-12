import io

import numpy as np

from plyfile import PlyData


def read_ply_file(path):
    mesh = PlyData.read(path)

    # Add two attributes for compatibility with existing code.
    mesh.vertices = []
    for v in mesh['vertex'].data:
        mesh.vertices.append([v['x'], v['y'], z_mult * v['z']])
    mesh.triangles = np.vstack(mesh['face'].data['vertex_index'])

    return mesh
