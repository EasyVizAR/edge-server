import csv
import glob
import os
import visualize_pointcloud as v
import numpy as np
import svgwrite

import open3d as o3d

if __name__ == "__main__":
    planepoints = []
    pointgroups = []
    linegroups = []
    mtime = {}

    for i, path in enumerate(glob.glob("HoloLensData/seventhfloor/*.ply")):
        # If the path is not in size, we want to look at it and put it in size
        # If the path is in size and the current size is larger than the previous size, we want to look at it
        # If the path is in size and the current size is equal to the previous size, we don't want to look at it

        mt = os.path.getmtime()
        if path not in mtime or mtime[path] < mt:
            mtime[path] = mt
            mesh = o3d.io.read_triangle_mesh(path)
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

    scale = 10
    dwg = svgwrite.Drawing('svgwrite-example.svg', profile='tiny')
    for i, group in enumerate(linegroups):
        for j, line in enumerate(group):
            p1f = ((line[0][0] - minx) * scale, (line[0][2] - minz) * scale)
            p2f = ((line[1][0] - minx) * scale, (line[1][2] - minz) * scale)
            dwg.add(dwg.line(start=p1f,
                             end=p2f,
                             stroke=svgwrite.rgb(0, 0, 255, '%')
                             )
                    )

    #print(dwg.tostring())
    dwg.save()
    print("Svg saved")


