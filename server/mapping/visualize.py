import csv
import glob
import visualize_pointcloud as v
import numpy as np
import svgwrite

import open3d as o3d

if __name__ == "__main__":
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    planepoints = []
    pointgroups = []
    linegroups = []

    for path in glob.glob("HoloLensData/seventhfloor/*.ply"):
        mesh = o3d.io.read_triangle_mesh(path)
        #mesh.compute_vertex_normals()
        zplane = v.isolate_zplane(mesh, 0, verticalz=False)
        #v.plotplanecoords(zplane[0], verticalz = False)
        #planepoints = planepoints + list(np.asarray(zplane[0].points))
        planepoints += zplane[0].points
        pointgroups.append(zplane[0].points)
        linegroups.append(zplane[2].lines)
        vis.add_geometry(zplane[2])

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
    v.plotplanecoords(planepoints, verticalz=False)
    planepoints = planepoints - np.asarray([minx, 0, minz])
    planepoints = imgrange/range*np.asarray(planepoints)
    #print(lines)

    #svglines = []
    dwg = svgwrite.Drawing('svgwrite-example.svg', profile='tiny')
    prevpoint = None
    for i, group in enumerate(pointgroups):
        for j, point in enumerate(group):
            xcoord = (point[0]-minx)*10
            ycoord = (point[2]-minz)*10
            if prevpoint is not None:
                #svglines.append([prevpoint, (xcoord, ycoord)])
                dwg.add(dwg.line(start=prevpoint,
                                 end=(xcoord, ycoord),
                                 stroke=svgwrite.rgb(0, 0, 255, '%')
                                 )
                        )
            prevpoint = (xcoord, ycoord)

    print(dwg.tostring())
    dwg.save()
    print("Svg saved?")

    v.plotplanecoords(planepoints, verticalz = False)

    path = o3d.geometry.PointCloud()
    points = []
    with open("seventhfloor/updates.csv", "r") as source:
        reader = csv.DictReader(source)
        for line in reader:
            points.append([float(v) for v in [line['x'], line['y'], line['z']]])
    path.points = o3d.utility.Vector3dVector(points)
    path.paint_uniform_color([0, 0, 1])
    vis.add_geometry(path)

    vis.run()
    vis.destroy_window()

