import io

import numpy as np

from plyfile import PlyData


def read_ply_file(path):
    mesh = PlyData.read(path)

    # Multiplying z values by -1 fixes older meshes that were in the opposite
    # handedness. Newer meshes that include the "System: unity" comment are
    # already in the expected coordinate system.
    z_mult = -1
    for comment in mesh.comments:
        if comment.lower() == "system: unity":
            z_mult = 1

    # Add two attributes for compatibility with existing code.
    mesh.vertices = []
    for v in mesh['vertex'].data:
        mesh.vertices.append([v['x'], v['y'], z_mult * v['z']])
    mesh.triangles = np.vstack(mesh['face'].data['vertex_index'])

    return mesh
