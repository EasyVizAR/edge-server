import pickle
import sys

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

    def __init__(self, mesh=None, graph=None, component_ids=None):
        self.mesh = mesh
        self.graph = graph
        self.component_ids = component_ids

    def component_distance(self, comp1, comp2, *args):
        """
        Compute distance between two components.

        The extra variable args makes this compatible with networkx functions
        including as the heuristic for astar_path.
        """
        point_a = self.graph.nodes[comp1]['center']
        point_b = self.graph.nodes[comp2]['center']
        return np.linalg.norm(point_a - point_b)

    def face_distance(self, face1, face2, *args):
        """
        Compute distance between two faces.

        The extra variable args makes this compatible with networkx functions
        including as the heuristic for astar_path.
        """
        point_a = self.mesh.triangles_center[face1]
        point_b = self.mesh.triangles_center[face2]
        return np.linalg.norm(point_a - point_b)

    def find_component(self, point):
        """
        Find the component immediately below the given point.

        Returns component index and intersection point or None.
        """
        face, location = self.find_face(point)
        if face is None:
            return None, None
        return self.component_ids[face], location

    def find_face(self, point):
        """
        Find the index of the face immediately below the given point.

        Returns face index and intersection point or None.
        """
        location, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=[point], ray_directions=[self.down], multiple_hits=False)
        if len(index_tri) == 0:
            return None, None
        return index_tri[0], location

    def find_path(self, start, end):
        """
        Find a walkable path between two points.
        """
        i, start_floor_point = self.find_component(start)
        j, end_floor_point = self.find_component(end)

        print("Find path from {} ({}) to {} ({})".format(start, i, end, j))

        if i is None:
            raise Exception("No component found below starting point")
        if j is None:
            raise Exception("No component found below ending point")

        path = nx.astar_path(self.graph, i, j, heuristic=self.component_distance)
        if path is None:
            path = []

        vertices = [start_floor_point.tolist()]

        # Skip the first and last vertices in the path. They are the centers of
        # the starting and ending mesh components, and we assume a person can
        # move freely within a component. Replacing the endpoints with the
        # desired start and end points should result in a nicer path.
        for x in path[1:-1]:
            vertices.append(self.graph.nodes[x]['center'].tolist())

        vertices.append(end_floor_point.tolist())

        return vertices

    def save(self, path):
        with open(path, "wb") as output:
            pickle.dump(self, output)

    def show(self):
        # Choose a random color for each component in the mesh and color the
        # faces.
        face_colors = dict()
        for i, comp_id in enumerate(self.component_ids):
            if comp_id not in face_colors:
                face_colors[comp_id] = np.random.randint(0, 192, size=(4,))
                face_colors[comp_id][3] = 192
            self.mesh.visual.face_colors[i] = face_colors[comp_id]

        color = [0, 0, 255, 255]

        lines = []
        for a, b in self.graph.edges:
            line = trimesh.path.entities.Line([a, b], color=color)
            lines.append(line)

        vertices = []
        for c in self.graph.nodes:
            vertices.append(self.graph.nodes[c]['center'])

        path = trimesh.path.path.Path3D(lines, vertices)

        scene = trimesh.Scene()
        scene.add_geometry(self.mesh)
        scene.add_geometry(path)
        scene.show()

    @classmethod
    def load(cls, path):
        with open(path, "rb") as source:
            return pickle.load(source)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <navmesh.pickle file>".format(sys.argv[0]))
        sys.exit(1)

    with open(sys.argv[1], "rb") as source:
        navmesh = pickle.load(source)

    print(navmesh)
    navmesh.show()
