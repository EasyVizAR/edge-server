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

    def __init__(self, _id):
        self.id = _id

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

    def find_boundary_faces(self, face):
        """
        Find the boundary faces of a component given one face on that component.
        """
        comp_id = self.component_id[face]
        comp_faces = self.components[comp_id]

        edge_indices = self.mesh.faces_unique_edges[comp_faces].reshape(-1)
        boundary_indices = trimesh.grouping.group_rows(edge_indices, require_count=1)

        output = set()
        for sel in boundary_indices:
            output.add(comp_faces[int(sel / 3)])

        return list(output)

    def find_closest_boundary_face(self, containing_face, target_point):
        """
        Find the boundary of the component containing a face and find the
        closest face on that boundary to a target point.
        """
        boundary = self.find_boundary_faces(containing_face)

        vertices = self.mesh.triangles_center[boundary]
        distances = np.linalg.norm(target_point - vertices, axis=1)
        min_ind = np.argmin(distances)
        return boundary[min_ind]

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

    def observed_transition(self, face1, face2):
        # If the two faces are adjacent, update the hit count, and we are done.
        # This should be a common condition.
        if self.neighbors.has_edge(face1, face2):
            hits = self.neighbors.edges[face1, face2].get("hits", 0) + 1
            self.neighbors.edges[face1, face2]['hits'] = hits

        # If they belong to the same chunk, we can try to find a path among
        # adjacent faces that connects them and label that as walkable. This
        # is a bit risky, as it might cross obstacles. We could add some
        # intersection detection here to be more careful.
        try:
            path = nx.astar_path(self.neighbors, face1, face2, heuristic=self.face_distance)
        except nx.NodeNotFound:
            return
        except nx.NetworkXNoPath:
            return

        for i in range(len(path) - 1):
            hits = self.neighbors.edges[path[i], path[i+1]].get("hits", 0) + 1
            self.neighbors.edges[path[i], path[i+1]]['hits'] = hits

    def save(self, path):
        with open(path, "wb") as output:
            pickle.dump(self, output)

    def set_mesh(self, mesh):
        self.mesh = mesh

        self.components, self.component_id = self.split_mesh(mesh)

        self.neighbors = nx.Graph()
        for a, b in mesh.face_adjacency:
            if mesh.face_normals[a, 1] >= walkable_threshold and mesh.face_normals[b, 1] >= walkable_threshold:
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
        fname = os.path.basename(path)
        chunk_id, ext = os.path.splitext(fname)

        chunk = cls(chunk_id)

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
