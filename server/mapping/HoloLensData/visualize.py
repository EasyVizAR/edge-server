import csv
import glob
import visualize_pointcloud as v
import numpy as np

import open3d as o3d

if __name__ == "__main__":
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    planepoints = []

    for path in glob.glob("seventhfloor/*.ply"):
        mesh = o3d.io.read_triangle_mesh(path)
        #mesh.compute_vertex_normals()
        zplane = v.isolate_zplane(mesh, 0, verticalz=False)
        #v.plotplanecoords(zplane[0], verticalz = False)
        #planepoints = planepoints + list(np.asarray(zplane[0].points))
        planepoints += list(np.asarray(zplane[0].points))
        vis.add_geometry(zplane[2])

    # Normalize planepoints
    #print(planepoints)
    #planepoints = v.flattenpoints(planepoints, verticalz = False)
    """minx = min(planepoints[:][0])
    maxx = max(planepoints[:][0])
    minz = min(planepoints[:][2])
    maxz = max(planepoints[:][2])"""

    minx = min([x[0] for x in planepoints])
    maxx = max([x[0] for x in planepoints])
    minz = min([x[2] for x in planepoints])
    maxz = max([x[2] for x in planepoints])

    print([minx, maxx, minz, maxz])
    midx = (maxx - minx)
    midz = (maxz - minz)
    print([midx, 0, midz])
    v.plotplanecoords(planepoints, verticalz=False)
    planepoints = planepoints - np.asarray([minx, 0, minz])
    #mean = np.mean(planepoints, axis=0)
    #print(mean)
    #planepoints = planepoints - mean
    #mean2 = np.mean(planepoints, axis=0)
    #print(mean2)

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

