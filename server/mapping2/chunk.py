import os
import pickle

import networkx as nx
import numpy as np
import trimesh


walkable_threshold = 0.5


class Chunk:
    """
    Map Chunk

    A chunk is one map fragment defined by a triangle mesh. The mesh may not be
    contiguous but instead have multiple connected components. The Chunk class
    computes and stores intermediate results such as face adjacency and
    distance, connected components or bodies, and wall inference. These results
    can be cached an reused by the global mapping algorithms so long as the
    underlying mesh has not changed.
    """

    up = np.array([0, 1, 0])

    def __init__(self):
        self.mesh = trimesh.Trimesh()
        self.neighbors = nx.Graph()

        self.components = []
        self.component_id = []

    def face_distance(self, face1, face2, *args):
        """
        Compute distance between two faces.

        The extra variable args makes this compatible with networkx functions
        including as the heuristic for astar_path.
        """
        point_a = self.mesh.triangles_center[face1]
        point_b = self.mesh.triangles_center[face2]
        return np.linalg.norm(point_a - point_b)

    def infer_walls(self, heights=[0]):
        paths = []
        for height in heights:
            # this is essentially the inner loop of trimesh.intersections.mesh_multiplane,
            # but their implementation includes some transformations that we do not need
            #
            # Also, the dot product is greatly simplified because we know we are intersecting
            # with horizontal planes. The dot product with the plane normal [0, 1, 0] simply
            # extracts the Y values from the vertices.
            origin = np.array([0, height, 0])
            dots = self.mesh.vertices[:, 1] - height

            walls = trimesh.intersections.mesh_plane(self.mesh, self.up, origin, cached_dots=dots)
            path = trimesh.load_path(walls)
            paths.append(path)

        return paths

    def save(self, path):
        with open(path, "wb") as output:
            pickle.dump(self, output)

    def set_mesh(self, mesh):
        self.mesh = mesh

        self.components, self.component_id = self.split_mesh(mesh)

        self.neighbors = nx.Graph()
        for a, b in mesh.face_adjacency:
            self.neighbors.add_edge(a, b, hits=0, weight=self.face_distance(a, b))

    @classmethod
    def load_from_cache(cls, path):
        with open(path, "rb") as source:
            chunk = pickle.load(source)
            return chunk

    @classmethod
    def load_from_cache_or_ply(cls, cache_path, ply_path):
        if not os.path.exists(cache_path) or os.path.getmtime(ply_path) > os.path.getmtime(cache_path):
            chunk = cls.load_from_ply_file(ply_path)
            chunk.save(cache_path)
            return chunk
        else:
            return cls.load_from_cache(cache_path)

    @classmethod
    def load_from_ply_file(cls, path):
        chunk = cls()

        mesh = trimesh.load(path)
        if isinstance(mesh, trimesh.Trimesh):
            chunk.set_mesh(mesh)

        return chunk

    @classmethod
    def split_mesh(cls, mesh):
        """
        Split mesh into connected components (bodies) by face adjacency.

        Returns an array of length N, where N is the number of faces,
        and the value is the the body ID.
        """
        edges = []
        for a, b in mesh.face_adjacency:
            if mesh.face_normals[a, 1] >= walkable_threshold and mesh.face_normals[b, 1] >= walkable_threshold:
                edges.append([a, b])

        components = trimesh.graph.connected_components(
                edges=edges,
                nodes=np.arange(len(mesh.faces)),
                min_len=1,
                engine='networkx')

        component_id = np.zeros(len(mesh.faces), dtype=int)

        for i, component in enumerate(components):
            component_id[component] = i

        return components, component_id
