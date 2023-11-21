import collections
import copy
import os

import networkx as nx
import numpy as np
import svgwrite
import trimesh

from .chunk import Chunk
from .navmesh import NavigationMesh


walkable_threshold = 0.5
min_layer_size = 1
min_height_clearance = 1
cylinder_radius = 0.2
max_connection_distance = 1


class LayerConfig:
    def __init__(self, height=0, svg_output=None):
        self.height = height
        self.svg_output = svg_output


def medial_axis_for_submesh(submesh):
    outline = submesh.outline()
    edges = outline.vertex_nodes
    vertices = outline.vertices[:, 0:3:2]
    path = trimesh.path.Path2D(**trimesh.path.exchange.misc.edges_to_path(edges, vertices))

    ma = path.medial_axis()

    path3d = to_3D(ma)
    rays = [[0, 1, 0]] * len(path3d.vertices)  # assuming all points on the mesh are positive to y=0

    origins = path3d.vertices[:]
    origins[:, 1] = -100

    # this looks like what I want
    triangle, index, loc = trimesh.ray.ray_triangle.ray_triangle_id(
        submesh.triangles, origins, rays, multiple_hits=False)

    mask = np.asarray([x for x, _ in sorted(zip(loc, index), key=lambda pair: pair[1])])

    path3d.vertices = mask

    return path3d


def to_3D(path_2d, transform=None):
    """
    Convert 2D path to 3D path on the XY plane.

    Parameters
    -------------
    transform : (4, 4) float
      If passed, will transform vertices.
      If not passed and 'to_3D' is in self.metadata
      that transform will be used.

    Returns
    -----------
    path_3D : Path3D
      3D version of current path
    """
    # if there is a stored 'to_3D' transform in metadata use it
    if transform is None and 'to_3D' in path_2d.metadata:
        transform = path_2d.metadata['to_3D']

    # copy vertices and stack with zeros from (n, 2) to (n, 3)
    x = path_2d.vertices[:, 0]
    z = path_2d.vertices[:, 1]
    y = np.zeros(len(path_2d.vertices))
    vertices = np.column_stack((x, y, z))

    import trimesh.transformations as tf
    if transform is not None:
        vertices = tf.transform_points(vertices,
                                       transform)
    # make sure everything is deep copied
    path_3D = trimesh.path.Path3D(entities=copy.deepcopy(path_2d.entities),
                     vertices=vertices,
                     metadata=copy.deepcopy(path_2d.metadata))
    return path_3D


class MeshSoup:
    up = np.array([0, 1, 0])
    down = np.array([0, -1, 0])

    def __init__(self):
        self.mesh = None


        self.chunks = []
        self.visited_chunks = set()

        # array, length is number of faces in mesh, index of origin surface
        self.chunk_id = []

        # array, length is number of faces in mesh, maps from global index into chunk index
        self.local_id = []


        # array, length = number of faces in mesh, index of body containing that face
        self.body_id = []

        self.lower = None
        self.upper = None

        # Three increasingly broad sets of faces.
        # visited: set of faces that include points in user traces
        # touched: set of faces that were sweeped by a cylinder
        # walkable: includes, recursively any adjacent faces that meet walkability requirements
        self.visited = set()
        self.touched = set()
        self.walkable = set()

        self.body_graph = nx.Graph()
        self.neighbor_graph = nx.Graph()
        self.surface_graph = nx.Graph()
        self.walkable_graph = nx.Graph()

    def create_navigation_mesh(self):
        graph = nx.Graph()

        offset = 0
        for i, chunk in enumerate(self.chunks):
            if i in self.visited_chunks:
                for a, b in chunk.neighbors.edges:
                    graph.add_edge(a+offset, b+offset, weight=chunk.neighbors.edges[a, b]['weight'])
            offset += len(chunk.mesh.faces)

        return NavigationMesh(self.mesh, graph)

    def face_distance(self, face1, face2, *args):
        point_a = self.mesh.triangles_center[face1]
        point_b = self.mesh.triangles_center[face2]
        return np.linalg.norm(point_a - point_b)

    def observed_transition(self, face1, face2):
        lface1 = self.local_id[face1]
        lface2 = self.local_id[face2]

        # Visited chunks.
        chunk1 = self.chunk_id[face1]
        chunk2 = self.chunk_id[face2]

        if chunk1 == chunk2:
            chunk = self.chunks[chunk1]

            # If the two faces are adjacent, update the hit count, and we are done.
            # This should be a common condition.
            if chunk.neighbors.has_edge(lface1, lface2):
                chunk.neighbors.edges[lface1, lface2]['hits'] += 1
                return

            # If they belong to the same chunk, we can try to find a path among
            # adjacent faces that connects them and label that as walkable. This
            # is a bit risky, as it might cross obstacles. We could add some
            # intersection detection here to be more careful.
            try:
                path = nx.astar_path(chunk.neighbors, lface1, lface2, heuristic=chunk.face_distance)
            except nx.NetworkXNoPath:
                return

            #self.touched.update(path)
            for i in range(len(path) - 1):
                hits = chunk.neighbors.edges[path[i], path[i+1]].get("hits", 0) + 1
                chunk.neighbors.add_edge(path[i], path[i+1], hits=hits, weight=chunk.face_distance(path[i], path[i+1]))

        # If they belong to different chunks, we should try to find
        # the boundary faces that connect the two chunks and stitch them.
        else:
            body1 = self.body_id[face1]
            body2 = self.body_id[face2]

            boundary1 = self.find_boundary_faces(body1)
            boundary2 = self.find_boundary_faces(body2)

            vertices1 = self.mesh.triangles_center[boundary1]
            vertices2 = self.mesh.triangles_center[boundary2]

            # Going from face1 on body1 to face2 on body2.
            # Find the boundary face on body1 that is closest to target point.
            # Assume we pathed from face1 to that boundary face, exit1.
            v = self.mesh.triangles_center[face2]
            distances = np.linalg.norm(v - vertices1, axis=1)
            min_ind = np.argmin(distances)
            exit1 = boundary1[min_ind]
            self.observed_transition(face1, exit1)

            # Then find the boundary face on body2 closest to exit1.
            # Assume we pathed from exit2 to the target point, face2.
            v = self.mesh.triangles_center[exit1]
            distances = np.linalg.norm(v - vertices2, axis=1)
            min_ind = np.argmin(distances)
            exit2 = boundary2[min_ind]
            self.observed_transition(exit2, face2)

            # TODO: save edge between exit1 and exit2 somewhere for the navmesh

    def add_trace(self, times, points, apply_cylinder=False):
        """
        Annotate the mesh using a trace (user position history).

        This updates the set of visited faces and walkability information based
        on transitions observed in the trace.
        """
        down = np.array([0, -1, 0])

        directions = np.tile(down, [len(points), 1])

        locations, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=points, ray_directions=directions, multiple_hits=False)

        self.visited.update(index_tri)
        self.visited_chunks.update(self.chunk_id[index_tri])

        # Even though the trace was in chronological order, for some reason
        # intersects_location returns them in a different order.
        sorted_rays = np.argsort(index_ray)

        for i in range(len(sorted_rays) - 1):
            # These are indices into (locations, index_ray, index_tri).
            u = sorted_rays[i]
            v = sorted_rays[i+1]

            # Visited faces in the mesh.
            face1 = index_tri[u]
            face2 = index_tri[v]

            # Check if the two points are in the same mesh face.
            if face1 == face2:
                continue

            # Intersection points with the mesh.
            hit1 = locations[u]
            hit2 = locations[v]

            # Check if the distance between the two points is great.
            dist = np.linalg.norm(hit1 - hit2)
            if dist > max_connection_distance:
                print("Skipping edge of distance {}".format(dist))
                continue

            # Visited bodies, may be in the same chunk or not.
            body1 = self.body_id[face1]
            body2 = self.body_id[face2]

            if body1 != body2:
                self.body_graph.add_edge(body1, body2, link=(face1, face2), points=(hit1, hit2))

            # Visited surfaces.
            surf1 = self.chunk_id[face1]
            surf2 = self.chunk_id[face2]

            self.observed_transition(face1, face2)

            # Check if we crossed between two different surfaces.
            if surf1 != surf2:
                self.surface_graph.add_edge(surf1, surf2, link=(face1, face2), points=(hit1, hit2))

        # Move a human-sized cylinder along the path and add any touched faces.
        # This helps improve fill holes in the walkable mesh, but it might also
        # do weird things like fall through the floor. It also slows things
        # down a bit.
        if apply_cylinder:
            theta = np.linspace(0, np.pi, 12)
            directions = np.tile(down, [len(theta), 1])
            for i in range(len(points)):
                cylinder = np.zeros((12, 3))
                cylinder[:, 0] = points[i, 0] + cylinder_radius * np.cos(theta)
                cylinder[:, 1] = points[i, 1]
                cylinder[:, 2] = points[i, 2] + cylinder_radius * np.sin(theta)
                locations, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=cylinder, ray_directions=directions, multiple_hits=False)
                self.touched.update(index_tri)

    def infer_walkable(self):
        """
        Update walkable set by flood filling adjacent faces starting from those
        that were visited or touched.
        """
        # All visited faces should probably be in the touched set as well,
        # but it is not guaranteed.
        work = set.union(self.visited, self.touched)

        completed = set()
        while len(work) > 0:
            i = work.pop()

            self.walkable.add(i)
            completed.add(i)

            for j in self.neighbor_graph.neighbors(i):
                if j in completed:
                    continue

                if j in self.touched or self.is_walkable(j):
                    self.walkable.add(j)
                    work.add(j)
                    if not self.walkable_graph.has_edge(i, j):
                        self.walkable_graph.add_edge(i, j, type="inferred")

    def infer_walls(self, layers):
        paths = []
        for i, layer in enumerate(layers):
            if layer.svg_output is not None:
                size = self.upper - self.lower
                viewBox="{} {} {} {}".format(self.lower[0], self.lower[2], size[0], size[2])

                dwg = svgwrite.Drawing(layer.svg_output, profile='tiny', viewBox=viewBox)

                # This transformation flips the image vertically to account for the
                # fact that SVG uses the convention that the image starts at the top
                # left corner with increasing coordinates down and to the right.
                # The vertical axis ends up being the opposite of our mapping system.
                transform_group = dwg.g(id="transform", transform="matrix(1 0 0 -1 0 {})".format(self.lower[2] + self.upper[2]))
                dwg.add(transform_group)

                wall_group = dwg.g(id="walls", fill="none", stroke='black', stroke_width=0.1)
                transform_group.add(wall_group)

                for j, chunk in enumerate(self.chunks):
                    chunk_group = dwg.g(id="chunk-{}".format(j))

                    path = chunk.infer_walls(heights=[layer.height])[0]
                    for entity in path.entities:
                        if len(entity.points) == 2:
                            a, b = entity.points
                            line = dwg.line(start=path.vertices[a, [0, 2]], end=path.vertices[b, [0, 2]])
                        else:
                            line = dwg.polyline(points=[path.vertices[x, [0, 2]] for x in entity.points])
                        chunk_group.add(line)

                    if len(chunk_group.elements) > 0:
                        wall_group.add(chunk_group)

                dwg.save(pretty=True)

        return paths

    def color_walkable(self):
        """
        Color the walkable faces of the mesh.

        This should be called after adding one or more traces and calling
        infer_walkable so that the various sets of faces have been updated.
        """
        self.mesh.visual.face_colors[:] = [96, 96, 96, 192]

        for i in range(len(self.mesh.faces)):
            if i in self.visited:
                self.mesh.visual.face_colors[i] = [0, 255, 0, 255]
            elif i in self.touched:
                self.mesh.visual.face_colors[i] = [128, 255, 0, 255]
            elif i in self.walkable:
                self.mesh.visual.face_colors[i] = [255, 255, 0, 255]

    def is_walkable(self, index):
        """
        Test if a given face is walkable based on slope and height clearance.
        """
        if self.mesh.face_normals[index, 1] < walkable_threshold:
            return False

        # Start from the center point of face at index and move up just a
        # little bit to avoid intersecting with the same face.
        point = self.mesh.triangles_center[index, :] + 0.001 * self.up
        location, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=[point], ray_directions=[self.up], multiple_hits=False)

        # No intersection, means no ceiling for all we know.
        if len(index_tri) == 0:
            return True

        # Otherwise, test height clearance.
        dist = np.linalg.norm(point - location)
        if dist < min_height_clearance:
            return False

        return True

    def find_face(self, point):
        """
        Find the index of the face immediately below the given point.

        Returns face index or None.
        """
        location, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=[point], ray_directions=[self.down], multiple_hits=False)
        if len(index_tri) == 0:
            return None
        return index_tri[0]

    def find_boundary_faces(self, body_id):
        faces = self.components[body_id]
        edge_indices = self.mesh.faces_unique_edges[faces].reshape(-1)
        boundary_indices = trimesh.grouping.group_rows(edge_indices, require_count=1)

        output = set()
        for sel in boundary_indices:
            output.add(faces[int(sel / 3)])

        return list(output)

    def find_boundary_edges(self, body_id):
        faces = self.components[body_id]
        edge_indices = self.mesh.faces_unique_edges[faces].reshape(-1)
        boundary_indices = trimesh.grouping.group_rows(edge_indices, require_count=1)

        sel = edge_indices[boundary_indices]
        boundary_edges = self.mesh.edges_unique[sel]
        return boundary_edges

    def closest_points_on_boundary(self, source, target):
        """
        Find the set of points on the target mesh's boundary that are closest
        to one or more of the points in the source mesh's boundary.
        """
        closest_indices = set()
        closest_points = set()
        closest_dist = np.inf

        source_boundary = self.find_boundary_edges(source)
        if len(source_boundary) == 0:
            return closest_dist, []

        target_boundary = self.find_boundary_edges(target)
        if len(target_boundary) == 0:
            return closest_dist, []

        # Take the midpoint on each of the boundary edges.
        # Anytime this midpoint is selected as the closest point,
        # add both the associated endpoints for that edge.
        target_vertices = 0.5 * (self.mesh.vertices[target_boundary[:, 0]] + self.mesh.vertices[target_boundary[:, 1]])

        # For each source boundary point, find the closest target boundary point
        # and add that to the set.
        for i in range(len(source_boundary)):
            v = self.mesh.vertices[source_boundary[i, 0], :]

            # distance between source point i and all of the target boundary points
            distances = np.linalg.norm(v - target_vertices, axis=1)

            min_ind = np.argmin(distances)
            closest_indices.add(min_ind)
            closest_points.add(target_boundary[min_ind, 0])
            closest_points.add(target_boundary[min_ind, 1])
            if distances[min_ind] < closest_dist:
                closest_dist = distances[min_ind]

        edges = target_boundary[list(closest_indices), :]
        return closest_dist, edges

    def extract_crossing_lines(self):
        vertices = []
        lines = []

        def add_edges(edges):
            for u, v in edges:
                vertices.append(self.mesh.vertices[u, :])
                vertices.append(self.mesh.vertices[v, :])
                inds = [len(vertices)-2, len(vertices)-1]
                line = trimesh.path.entities.Line(inds, color=[0, 96, 0, 255])
                lines.append(line)

        paths = []
        for a, b in self.body_graph.edges:
            dist, edges = self.closest_points_on_boundary(a, b)
            add_edges(edges)

            dist, edges = self.closest_points_on_boundary(b, a)
            add_edges(edges)

        return trimesh.path.path.Path3D(lines, np.array(vertices))

    def print_mesh_info(self):
        print("Mesh: {}".format(self.mesh))
        for x in ["edges_sorted", "edges_unique", "edges_face", "faces_unique_edges"]:
            print("  {}: {}".format(x, getattr(self.mesh, x).shape))

    def get_bounding_box(self):
        size = self.upper - self.lower
        dims = {
            "left": self.lower[0],
            "top": self.lower[2],
            "width": size[0],
            "height": size[2]
        }
        return dims

    @classmethod
    def split_mesh(cls, mesh):
        """
        Split mesh into connected components (bodies) by face adjacency.

        Returns an array of length N, where N is the number of faces,
        and the value is the the body ID.
        """
        edges = []
        for a, b in mesh.face_adjacency:
            if mesh.face_normals[a, 1] >= walkable_threshold and mesh.face_normals[b, 1]:
                edges.append([a, b])

        components = trimesh.graph.connected_components(
                edges=edges,
                nodes=np.arange(len(mesh.faces)),
                min_len=1,
                engine='networkx')

        body_indices = np.zeros(len(mesh.faces), dtype=int)

        for i, component in enumerate(components):
            body_indices[component] = i

        return components, body_indices

    @classmethod
    def from_directory(cls, dir_path):
        soup = cls()

        origins = []
        meshes = []
        for i, fname in enumerate(os.listdir(dir_path)):
            path = os.path.join(dir_path, fname)
            chunk = Chunk.load_from_ply_file(path)
            soup.chunks.append(chunk)
            meshes.append(chunk.mesh)
            origins.extend([i] * len(chunk.mesh.faces))

        soup.chunk_id = np.array(origins)

        soup.mesh = trimesh.util.concatenate(meshes)

        soup.lower = np.min(soup.mesh.vertices, axis=0)
        soup.upper = np.max(soup.mesh.vertices, axis=0)

        return soup

    @classmethod
    def from_meshes(cls, meshes):
        soup = cls()

        origins = []
        for i, mesh in enumerate(meshes):
            soup.surface_graph.add_node(i, centroid=mesh.centroid)
            origins.extend([i] * len(mesh.faces))

            chunk = Chunk()
            chunk.set_mesh(mesh)
            soup.chunks.append(chunk)

        soup.chunk_id = np.array(origins)

        soup.mesh = trimesh.util.concatenate(meshes)
        soup.components, soup.body_id = cls.split_mesh(soup.mesh)

        soup.lower = np.min(soup.mesh.vertices, axis=0)
        soup.upper = np.max(soup.mesh.vertices, axis=0)

        for i in range(len(soup.mesh.faces)):
            soup.walkable_graph.add_node(i, center=soup.mesh.triangles_center[i])

        soup.neighbor_graph.add_edges_from(soup.mesh.face_adjacency)

        return soup
