import math

import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import sympy as sm

# Removing points with vector normals in specific directions
def remove_normals(pcd):
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    # print(pcd)
    # print(np.asarray(pcd.points))
    #o3d.visualization.draw_geometries([pcd])

    normals = np.asarray(pcd.normals)
    pcdnp = np.asarray(pcd.points)

    print(pcdnp)

    updatedarray = []
    updatednormals = []
    boundary = math.cos(60 * (math.pi / 180))
    removed_points = 0

    print("Finding good points...")
    for i in range(len(normals)):
        if not(abs(normals[i, 0]) < boundary and abs(normals[i, 1]) < boundary):
            updatedarray.append(pcdnp[i])
            updatednormals.append(normals[i])
        removed_points += 1
    print("{} points removed".format(removed_points))
    print("Good points found...")

    print(np.shape(updatedarray))
    # print(np.ones((10, 10)))

    updatedpcd = o3d.geometry.PointCloud()
    updatedpcd.points = o3d.utility.Vector3dVector(updatedarray)
    updatedpcd.normals = o3d.utility.Vector3dVector(updatednormals)
    #o3d.visualization.draw_geometries([updatedpcd])
    return updatedpcd


def generate_pcd_data():
    x = np.linspace(-3, 3, 401)
    mesh_x, mesh_y = np.meshgrid(x, x)
    z = np.sinc((np.power(mesh_x, 2) + np.power(mesh_y, 2)))
    z_norm = (z - z.min()) / (z.max() - z.min())
    xyz = np.zeros((np.size(mesh_x), 3))
    xyz[:, 0] = np.reshape(mesh_x, -1)
    xyz[:, 1] = np.reshape(mesh_y, -1)
    xyz[:, 2] = np.reshape(z_norm, -1)
    print('xyz')
    print(xyz)
    generatedpcd = o3d.geometry.PointCloud()
    generatedpcd.points = o3d.utility.Vector3dVector(xyz)
    o3d.visualization.draw_geometries([generatedpcd])

# Showing density of points in a specific axis
def histogram(pcd):
    pcdnp = np.asarray(pcd.points)
    # print(pcdnp[:, 1])
    plt.hist(pcdnp[:, 2], density=True, bins=30)
    plt.show()

def flatten(pcd):
    pcdnp = np.asarray(moredownpcd.points)
    for i in range(len(pcdnp)):
        pcdnp[i, 2] = 0

    flatpcd = o3d.geometry.PointCloud()
    flatpcd.points = o3d.utility.Vector3dVector(pcdnp)
    #o3d.visualization.draw_geometries([flatpcd])
    return flatpcd

def flattenpoints(points, verticalz = True):
    if verticalz:
        vert = 2
    else:
        vert = 1
    for i in range(len(points)):
        points[i][vert] = 0

def plane_segmentation(pcd):
    plane_model, inliers = pcd.segment_plane(distance_threshold=0.05,
                                                     ransac_n=3,
                                                     num_iterations=1000)
    [a, b, c, d] = plane_model
    print(f"Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")

    inlier_cloud = pcd.select_by_index(inliers)
    inlier_cloud.paint_uniform_color([1.0, 0, 0])
    outlier_cloud = pcd.select_by_index(inliers, invert=True)
    # o3d.visualization.draw_geometries([inlier_cloud, outlier_cloud])
    o3d.visualization.draw_geometries([inlier_cloud])

def mesh(pcd):
    # Why not just estimate normals and put them into pcd.normals?
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    radius = 3 * avg_dist

    bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector(
        [radius, radius * 2]))

    dec_mesh = o3d.geometry.TriangleMesh.simplify_quadric_decimation(100000)

    dec_mesh.remove_degenerate_triangles()
    dec_mesh.remove_duplicated_triangles()
    dec_mesh.remove_duplicated_vertices()
    dec_mesh.remove_non_manifold_edges()

    o3d.visualization.draw_geometries(dec_mesh)

    """ Error at TriangleMesh create point cloud method
        [Open3D Error] (class std::shared_ptr<class open3d::geometry::TriangleMesh> __cdecl open3d::geometry::BallPivoting::Run(const class std::vector<double,class std::allocator<double> > &)) D:\a\Open3D\Open3D\cpp\open3d\geometry\SurfaceReconstructionBallPivoting.cpp:670: ReconstructBallPivoting requires normals

    Traceback (most recent call last):
      File "C:/Users/rudyb/OneDrive/Code/Research/visualize_pointcloud.py", line 26, in <module>
        bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector([radius, radius * 2]))
    RuntimeError: [Open3D Error] (class std::shared_ptr<class open3d::geometry::TriangleMesh> __cdecl open3d::geometry::BallPivoting::Run(const class std::vector<double,class std::allocator<double> > &)) D:\a\Open3D\Open3D\cpp\open3d\geometry\SurfaceReconstructionBallPivoting.cpp:670: ReconstructBallPivoting requires normals
        """

def isolate_zplane(mesh, vertical, verticalz = True):
    points = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)

    newpoints = []
    tripoints = []

    #print(len(points))
    #print(len(triangles))
    vaxis = 0
    vnorm = []
    if verticalz:
        vaxis = 2
    else:
        vaxis = 1
    vnorm = [0, abs(vaxis-2), abs(vaxis-1)]
    vcord = [x*vertical for x in vnorm]

    lines = []
    pointindex = 0

    # iterate through list of triangle arrays
    # triangle array = [point 1, point 2, point 3]
    for i in range(len(triangles)):
        intersect = False
        intersecting = []

        for j in range(3):
            p0 = points[triangles[i, j]]
            p1 = points[triangles[i, (j+1)%3]]
            b = (p0[vaxis] > vertical > p1[vaxis]) or (p0[vaxis] < vertical < p1[vaxis])
            plane_splits_edge = splitpoints(p0, p1, vcord, vnorm)
            if b != plane_splits_edge:
                print("Uh oh shitteroo")
            if plane_splits_edge:
                pi = lp_intersect(p0, p1, vcord, vnorm)
                newpoints.append(pi)
                intersect = True
                intersecting.append(pointindex)
                pointindex += 1
                #print("Gotem")

        #print(len(intersecting))
        if len(intersecting) == 2:
            lines.append([intersecting[0], intersecting[1]])

        if intersect:
            tripoints.append(points[triangles[i, 0]])
            tripoints.append(points[triangles[i, 1]])
            tripoints.append(points[triangles[i, 2]])

    #for i in range(3):
    #    print(points[triangles[1000, i]])

    #print(len(lines))
    #print(len(newpoints))
    #print(lines)
    #print(np.asarray(lines))

    colors = [[1, 0, 0] for i in range(len(lines))]
    lineset = o3d.geometry.LineSet()
    lineset.points = o3d.utility.Vector3dVector(newpoints)
    lineset.lines = o3d.utility.Vector2iVector(np.asarray(lines))
    lineset.colors = o3d.utility.Vector3dVector(colors)

    pcdnew = o3d.geometry.PointCloud()
    pcdtri = o3d.geometry.PointCloud()
    pcdnew.points = o3d.utility.Vector3dVector(newpoints)
    pcdnew.paint_uniform_color([1, 0, 0])
    pcdtri.points = o3d.utility.Vector3dVector(tripoints)
    pcdtri.paint_uniform_color([0, 0, 1])

    return pcdnew, pcdtri, lineset

def lp_intersect(p0, p1, p_co, p_no, epsilon=1e-6):
    """
    p0, p1: Define the line.
    p_co, p_no: define the plane:
        p_co Is a point on the plane (plane coordinate).
        p_no Is a normal vector defining the plane direction;
             (does not need to be normalized).

    Return a Vector or None (when the intersection can't be found).
    """

    u = np.subtract(p1, p0)
    dot = np.dot(p_no, u)

    # In this case, epsilon is an error bound of some type where if the dot product is close to 0 (difference < epsilon)
    # , then the point and plane are parallel

    if abs(dot) > epsilon:
        # The factor of the point between p0 -> p1 (0 - 1)
        # if 'fac' is between (0 - 1) the point intersects with the segment.
        # Otherwise:
        #  < 0.0: behind p0.
        #  > 1.0: infront of p1.
        w = np.subtract(p0, p_co)
        fac = -1*np.dot(p_no, w) / dot
        u = u * fac
        return np.add(p0, u)

    # The segment is parallel to plane.
    return None

def planeside(p0, pcord, pnorm):
    return np.dot(p0, pnorm) - np.dot(pcord, pnorm)

def splitpoints(p0, p1, pcord, pnorm):
    v0 = np.dot(p0, pnorm) - np.dot(pcord, pnorm)
    v1 = np.dot(p1, pnorm) - np.dot(pcord, pnorm)
    return True if v0*v1 <= 0 else False

def plotplanecoords(points, verticalz=True):
    if verticalz:
        planey = 1
    else:
        planey = 2
    px = [x[0] for x in points]
    py = [-1*x[planey] for x in points]
    plt.scatter(px, py)
    plt.show()

if __name__ == "__main__":

    # Enable webrtc visualization
    #o3d.visualization.webrtc_server.enable_webrtc()

    print("Load a .pcd point cloud, print it, and render it")
    #ptcloud1 = "./2011-11-28_20.58.03-info.tar/2011-11-28_20.58.03/pointcloud.pcd"
    ptcloud2 = "./2011-12-17_15.02.56-pointcloud/2011-12-17_15.02.56/pointcloud.pcd"
    pcd = o3d.io.read_point_cloud(ptcloud2)
    #o3d.visualization.draw_geometries([pcd])

    downpcd = pcd.voxel_down_sample(voxel_size=0.05)
    #print(downpcd)
    #print(np.asarray(downpcd.points))
    #o3d.visualization.draw_geometries([downpcd])

    moredownpcd = downpcd.voxel_down_sample(voxel_size=0.05)

    norm = remove_normals(downpcd)
    flatnorm = flatten(norm)

    o3d.visualization.draw_geometries([flatnorm])

