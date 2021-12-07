import open3d as o3d
import numpy as np

import visualize_pointcloud
from sympy import Point3D, Plane
import svgwrite

if __name__ == "__main__":
    """
    o3d.visualization.webrtc_server.enable_webrtc()
    cube_red = o3d.geometry.TriangleMesh.create_box(1, 2, 4)
    cube_red.compute_vertex_normals()
    cube_red.paint_uniform_color((1.0, 0.0, 0.0))
    o3d.visualization.draw(cube_red)"""

    #mesh = o3d.geometry.TriangleMesh.create_sphere(1, create_uv_map=True)
    #lines = o3d.geometry.LineSet.create_from_triangle_mesh(mesh)
    #zpoints = visualize_pointcloud.isolate_zplane(mesh, 0.5)
    """o3d.visualization.draw_geometries([zpoints[0], zpoints[1], zpoints[2], lines])"""
    #visualize_pointcloud.plotplanecoords(zpoints[0])

    """plane = Plane(Point3D([2, 0, 0]), Point3D([0, 2, 0]), Point3D([0, 0, 2]))
    pointList = [
        [2, 2, 2],
        [0, 0, 0]
    ]
    print(plane)
    for point in pointList:
        print(point)
        print(planeside(point, [1, 1, 1], [1, 1, 1]))"""
    """if plane.equation(x=point[0], y=point[1], z=point[2]) > 0:
            print
            "point is on side A"
        else:
            print
            "point is on side B" """
