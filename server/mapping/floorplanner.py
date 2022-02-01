import csv
import glob
import json
import math
import os

import numpy as np
import svgwrite

from .plyutil import read_ply_file


def splitpoints(p0, p1, pcord, pnorm):
    v0 = np.dot(p0, pnorm) - np.dot(pcord, pnorm)
    v1 = np.dot(p1, pnorm) - np.dot(pcord, pnorm)

    # If v0 and v1 are different signs, where one is positive and the other is negative
    # , then they are on opposite sides of the plane.
    return True if v0 * v1 <= 0 else False


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
        fac = -1 * np.dot(p_no, w) / dot
        u = u * fac
        return np.add(p0, u)

    # The segment is parallel to plane.
    return None


class Floorplanner:

    def __init__(self, raw_ply_path, image_scale=1, json_data_path=None):
        self.raw_ply_path = raw_ply_path
        self.image_scale = image_scale
        self.json_data_path = json_data_path
        self.data = {}
        self.first_load_json = json_data_path is not None

    def calculate_intersections(self, mesh, headset_position=[0, 0, 0], vector_normal=[0, 1, 0], json_serialize=False):
        points = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)

        lines = []

        # iterate through list of triangle arrays
        # triangle array = [point 1, point 2, point 3]
        for i in range(len(triangles)):
            intersecting_points = []

            for j in range(3):
                p0 = points[triangles[i, j]]
                p1 = points[triangles[i, (j + 1) % 3]]
                plane_splits_edge = splitpoints(p0, p1, headset_position, vector_normal)
                if plane_splits_edge:
                    pi = lp_intersect(p0, p1, headset_position, vector_normal)
                    if json_serialize:
                        intersecting_points.append(pi.tolist())
                    else:
                        intersecting_points.append(pi)

            if len(intersecting_points) == 2:
                lines.append([intersecting_points[0], intersecting_points[1]])

        return lines

    def update_lines(self, initialize=True):
        if initialize:
            self.data = {}
        elif self.first_load_json and os.path.exists(self.json_data_path):
            with open(self.json_data_path, 'r') as f:
                self.data = json.load(f)
            self.first_load_json = False

        changes = 0
        for i, path in enumerate(glob.glob(self.raw_ply_path)):
            time_of_prev_mod = os.path.getmtime(path)
            update_lines_at_path = path not in self.data or self.data[path]["last_modified"] < time_of_prev_mod
            if initialize or update_lines_at_path:
                mesh = read_ply_file(path)
                zplane = self.calculate_intersections(mesh, json_serialize=True)
                self.data[path] = {"last_modified": time_of_prev_mod, "lines": zplane}
                changes += 1

        if (initialize or changes > 0) and self.json_data_path is not None:
            with open(self.json_data_path, 'w') as f:
                json.dump(self.data, f)
                print("Map updated with {} surfaces changed".format(changes))

        return changes

    def write_image(self, svg_destination_path):
        """
        Write map image file as an SVG.
        """
        minx = maxx = minz = maxz = 0
        for path in self.data:
            for segment in self.data[path]['lines']:
                for point in segment:
                    minx = min(point[0], minx)
                    maxx = max(point[0], maxx)
                    minz = min(point[2], minz)
                    maxz = max(point[2], maxz)

        scale = self.image_scale
        image_width = scale * (maxx - minx)
        image_height = scale * (maxz - minz)

        dwg = svgwrite.Drawing(svg_destination_path, profile='tiny',
                viewBox="{} {} {} {}".format(scale*minx, scale*minz, image_width, image_height))
        for path in self.data:
            for line in self.data[path]["lines"]:
                p1f = ((line[0][0]) * scale, (line[0][2]) * scale)
                p2f = ((line[1][0]) * scale, (line[1][2]) * scale)
                dwg.add(dwg.line(start=p1f, end=p2f, stroke='black', stroke_width=0.1))
        dwg.save()


if __name__ == '__main__':
    fp = Floorplanner("seventhfloor/*.ply", json_data_path='data.json')
    fp.update_lines(initialize=True)
    fp.write_image('svgwrite-example.svg')
