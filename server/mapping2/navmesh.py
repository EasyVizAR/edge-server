import pickle

import networkx as nx
import numpy as np
import trimesh


class NavigationMesh:
    """
    Data structure used for pathfinding.

    The NavigationMesh contains both a mesh and a graph.  The mesh contains
    walkable surfaces, such that if we raycast down from a given user location,
    we can find a corresponding point in the mesh.  The graph gives valid
    transitions between mesh cells and can be used for A* search.
    """

    down = np.array([0, -1, 0])

    def __init__(self, mesh=None, graph=None):
        self.mesh = mesh
        self.graph = graph

    def face_distance(self, face1, face2, *args):
        """
        Compute distance between two faces.

        The extra variable args makes this compatible with networkx functions
        including as the heuristic for astar_path.
        """
        point_a = self.mesh.triangles_center[face1]
        point_b = self.mesh.triangles_center[face2]
        return np.linalg.norm(point_a - point_b)

    def find_face(self, point):
        """
        Find the index of the face immediately below the given point.

        Returns face index or None.
        """
        location, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=[point], ray_directions=[self.down], multiple_hits=False)
        if len(index_tri) == 0:
            return None
        return index_tri[0]

    def find_path(self, start, end):
        """
        Find a walkable path between two points.
        """
        i = self.find_face(start)
        j = self.find_face(end)

        print("Find path from {} ({}) to {} ({})".format(start, i, end, j))

        if i is None:
            raise Exception("No face found below starting point")
        if j is None:
            raise Exception("No face found below ending point")

        path = nx.astar_path(self.graph, i, j, heuristic=self.face_distance)

        vertices = []
        for x in path:
            vertices.append(self.mesh.triangles_center[x])

        return vertices

    def save(self, path):
        with open(path, "wb") as output:
            pickle.dump(self, output)

    def show(self):
        lines = []
        for a, b in self.graph.edges:
            confidence = self.graph.edges[a, b].get("confidence", 0.5)
            color = [0, 0, int(confidence * 255), 255]
            line = trimesh.path.entities.Line([a, b], color=color)
            lines.append(line)
        path = trimesh.path.path.Path3D(lines, self.mesh.triangles_center)

        scene = trimesh.Scene()
        scene.add_geometry(self.mesh)
        scene.add_geometry(path)
        scene.show()

    @classmethod
    def load(cls, path):
        with open(path, "rb") as source:
            return pickle.load(source)
