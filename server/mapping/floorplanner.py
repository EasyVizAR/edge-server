import csv
import glob
import json
import math
import os

import networkx as nx
import numpy as np
import svgwrite

from .plyutil import read_ply_file


def calculate_dot_plane(points, headset_position, plane_normal):
    """
    Calculate dot product of each triangle point with the cutting plane.

    These values will be used to test if edges cross the cutting plane.
    However, it is faster to compute this dot product once for each point in
    the mesh, since the dot product will need to be used for each edge out of
    the point (at least twice).
    """
    plane = np.dot(headset_position, plane_normal)

    pdotplane = []
    for p in points:
        pdotplane.append(np.dot(p, plane_normal) - plane)

    return pdotplane


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

    def __init__(self, ply_path_or_list, image_scale=1, json_data_path=None, headsets=None):
        self.ply_path_or_list = ply_path_or_list
        self.image_scale = image_scale
        self.json_data_path = json_data_path
        self.data = {}
        self.first_load_json = json_data_path is not None
        self.headsets = headsets

    def calculate_intersections(self, mesh, headset_position=[0, 0, 0], vector_normal=[0, 1, 0], json_serialize=False):
        points = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)

        paths = []

        # We will construct a graph, where each node represents an intersection
        # point along the edge of a triangle. Each triangle should have two
        # intersection points, which will be connected by an edge in the graph,
        # and later, a line segment in the map.
        graph = nx.Graph()

        pdotplane = calculate_dot_plane(points, headset_position, vector_normal)

        # iterate through list of triangle arrays
        # triangle array = [point 1, point 2, point 3]
        for i in range(len(triangles)):
            nodes = []

            for j in range(3):
                v0 = pdotplane[triangles[i, j]]
                v1 = pdotplane[triangles[i, (j + 1) % 3]]

                # The line segment intersects with the cutting plane if this
                # product is negative, meaning v0 and v1 have opposite signs.
                if v0 * v1 <= 0:
                    # These are integer point indices that identify the
                    # edge of the triangle.
                    p0 = triangles[i, j]
                    p1 = triangles[i, (j + 1) % 3]

                    node = (p0, p1)
                    if p0 < p1:
                        node = (p0, p1)
                    else:
                        node = (p1, p0)

                    nodes.append(node)

            if len(nodes) == 2:
                graph.add_node(nodes[0])
                graph.add_node(nodes[1])
                graph.add_edge(nodes[0], nodes[1])

        # Each connected component in the graph corresponds to a list of points
        # that can become a polyline in the SVG output.
        for component in nx.connected_components(graph):
            output_path = []

            subgraph = graph.subgraph(component).copy()

            path_length = 0
            longest_path = 0

            # Find all shortest paths between pairs of points in the subgraph.
            # Then find the longest shortest path, which we will use for the
            # output.
            all_shortest_paths = nx.shortest_path(subgraph)
            for s in all_shortest_paths.keys():
                for t in all_shortest_paths[s].keys():
                    if len(all_shortest_paths[s][t]) > path_length:
                        path_length = len(all_shortest_paths[s][t])
                        longest_path = all_shortest_paths[s][t]

            # Recall that each node in the graph corresponds to an
            # edge of a triangle. Here is where we look back at the
            # mesh and calculate the point of intersection with the
            # cutting plane.
            for node in longest_path:
                p0 = points[node[0]]
                p1 = points[node[1]]
                pi = lp_intersect(p0, p1, headset_position, vector_normal)
                output_path.append(pi.tolist())

            paths.append(output_path)

        return paths

    def update_lines(self, initialize=True):
        if initialize:
            self.data = {}
        elif self.first_load_json and os.path.exists(self.json_data_path):
            with open(self.json_data_path, 'r') as f:
                self.data = json.load(f)
            self.first_load_json = False

        changes = 0

        if isinstance(self.ply_path_or_list, str):
            self.ply_path_or_list = glob.glob(self.ply_path_or_list)

        # Detect surface files that have been deleted and stop using line
        # segments that were created from them.
        deleted = []
        for path in self.data.keys():
            if not os.path.exists(path):
                deleted.append(path)
        for path in deleted:
            self.data.pop(path)
            changes += 1

        for i, path in enumerate(self.ply_path_or_list):
            time_of_prev_mod = os.path.getmtime(path)
            update_lines_at_path = path not in self.data or self.data[path]["last_modified"] < time_of_prev_mod
            if initialize or update_lines_at_path:
                mesh = read_ply_file(path)
                zplane = self.calculate_intersections(mesh, json_serialize=True)
                self.data[path] = {"last_modified": time_of_prev_mod, "polylines": zplane}
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
            for segment in self.data[path].get('lines', []):
                for point in segment:
                    minx = min(point[0], minx)
                    maxx = max(point[0], maxx)
                    minz = min(point[2], minz)
                    maxz = max(point[2], maxz)

            for polyline in self.data[path].get('polylines', []):
                for point in polyline:
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
            for line in self.data[path].get("lines", []):
                p1f = ((line[0][0]) * scale, (line[0][2]) * scale)
                p2f = ((line[1][0]) * scale, (line[1][2]) * scale)
                dwg.add(dwg.line(start=p1f, end=p2f, stroke='black', stroke_width=0.1))

            for polyline in self.data[path].get("polylines", []):
                dwg.add(dwg.polyline(
                    points=[(x[0], x[2]) for x in polyline],
                    stroke='black', stroke_width=0.1, fill="none"))

        # If floorplanner was configured with a headset list, draw some simple
        # markers over the map. This should ideally be a lot more configurable.
        if self.headsets is not None:
            for headset in self.headsets:
                dwg.add(dwg.circle(center=(headset.position.x, headset.position.z),
                    fill=headset.color,
                    fill_opacity=0.25,
                    r=1.0,
                    stroke=headset.color,
                    stroke_width=0.35
                ))

        dwg.save()

        return dict(left=scale*minx, top=scale*minz, width=image_width, height=image_height)


if __name__ == '__main__':
    fp = Floorplanner("seventhfloor/*.ply", json_data_path='data.json')
    fp.update_lines(initialize=True)
    fp.write_image('svgwrite-example.svg')
