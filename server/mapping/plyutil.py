import io

import numpy as np

from plyfile import PlyData


def read_ply_file(path):
    stream = io.BytesIO()

    # Reformat the PLY file because plyfile expects one triangle per line,
    # and we have some data files that were not formatted properly.
    with open(path, 'r') as source:
        for line in source:
            if len(line) >= 60 and line.startswith("3 "):
                words = line.strip().split()
                for i in range(int(len(words) / 4)):
                    start = i * 4
                    line = " ".join(words[start:start+4]) + "\n"
                    stream.write(line.encode('utf8'))
            else:
                stream.write(line.encode('utf8'))

    stream.seek(0)
    try:
        mesh = PlyData.read(stream)
    except:
        return None

    # Add two attributes for compatibility with existing code.
    mesh.vertices = []
    for v in mesh['vertex'].data:
        mesh.vertices.append([v['x'], v['y'], v['z']])
    mesh.triangles = np.vstack(mesh['face'].data['vertex_index'])

    return mesh
