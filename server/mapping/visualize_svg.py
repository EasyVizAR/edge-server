import csv
import glob
import io
import os

import numpy as np
import svgwrite

# Open3D is nice, but it is a pretty bulky library.
# It also requires libGL, which does not work on some of our test hardware.
USE_OPEN3D = False
if USE_OPEN3D:
    import open3d as o3d
else:
    from plyfile import PlyData

from . import visualize_pointcloud as v


def read_ply(path):
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
    mesh = PlyData.read(stream)

    # Add two attributes for compatibility with existing code.
    mesh.vertices = []
    for v in mesh['vertex'].data:
        mesh.vertices.append([v['x'], v['y'], v['z']])
    mesh.triangles = np.vstack(mesh['face'].data['vertex_index'])

    return mesh


def create_topdown_svg(surface_dir, output_path):
    planepoints = []
    pointgroups = []
    linegroups = []
    mtime = {}

    for i, path in enumerate(glob.glob(os.path.join(surface_dir, "*.ply"))):
        # If the path is not in size, we want to look at it and put it in size
        # If the path is in size and the current size is larger than the previous size, we want to look at it
        # If the path is in size and the current size is equal to the previous size, we don't want to look at it

        mt = os.path.getmtime(path)
        if path not in mtime or mtime[path] < mt:
            mtime[path] = mt
            if USE_OPEN3D:
                mesh = o3d.io.read_triangle_mesh(path)
            else:
                mesh = read_ply(path)
            zplane = v.slice(mesh, 0, verticalz=False)
            planepoints.extend(zplane[0])
            #pointgroups.append(zplane[0])
            #linegroups.append(zplane[2])
            linegroups.append(zplane[1])
            if i % 10 == 0:
                print(i)

    # Normalize planepoints
    #print(planepoints)
    #planepoints = v.flattenpoints(planepoints, verticalz = False)


    minx = min([x[0] for x in planepoints])
    maxx = max([x[0] for x in planepoints])
    minz = min([x[2] for x in planepoints])
    maxz = max([x[2] for x in planepoints])

    print([minx, maxx, minz, maxz])
    rangex = maxx - minx
    rangez = maxz - minz
    print([rangex, rangez])
    imgrange = 300
    range = max(rangex, rangez)

    scale = 1
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=(rangex, rangez))
    for i, group in enumerate(linegroups):
        for j, line in enumerate(group):
            p1f = ((line[0][0] - minx) * scale, (line[0][2] - minz) * scale)
            p2f = ((line[1][0] - minx) * scale, (line[1][2] - minz) * scale)
            dwg.add(dwg.line(start=p1f,
                             end=p2f,
                             stroke='black',
                             stroke_width='0.1'
                             )
                    )

    #print(dwg.tostring())
    dwg.save()
    print("Svg saved")


if __name__ == "__main__":
    create_topdown_svg("HoloLensData/seventhfloor", "svgwrite-example.svg")
