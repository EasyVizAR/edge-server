import math

import numpy as np


def flattenpoints(points, verticalz = True):
    if verticalz:
        vert = 2
    else:
        vert = 1
    for i in range(len(points)):
        points[i][vert] = 0

def slice(mesh, vertical, verticalz = True, json_serialize=False):
    points = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)

    newpoints = []
    #tripoints = []

    vaxis = 0
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
        #intersect = False
        #intersecting = []
        intersecting_points = []

        for j in range(3):
            p0 = points[triangles[i, j]]
            p1 = points[triangles[i, (j+1)%3]]
            #b = (p0[vaxis] > vertical > p1[vaxis]) or (p0[vaxis] < vertical < p1[vaxis])
            plane_splits_edge = splitpoints(p0, p1, vcord, vnorm)
            #if b != plane_splits_edge:
            #    print("Uh oh shitteroo")
            if plane_splits_edge:
                pi = lp_intersect(p0, p1, vcord, vnorm)
                if json_serialize:
                    newpoints.append(pi.tolist())
                    intersecting_points.append(pi.tolist())
                else:
                    newpoints.append(pi)
                    intersecting_points.append(pi)
                #intersect = True
                #intersecting.append(pointindex)
                #pointindex += 1
                #print("Gotem")

        #print(len(intersecting))
        if len(intersecting_points) == 2:
            lines.append([intersecting_points[0], intersecting_points[1]])

        """if intersect:
            tripoints.append(points[triangles[i, 0]])
            tripoints.append(points[triangles[i, 1]])
            tripoints.append(points[triangles[i, 2]])"""

    return newpoints, lines

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
