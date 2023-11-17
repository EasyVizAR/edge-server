import collections
import copy
import os

import networkx as nx
import numpy as np
import svgwrite
import trimesh


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

        # array, length is number of faces in mesh, index of origin surface
        self.origin_id = []

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

    def face_distance(self, face1, face2, *args):
        point_a = self.mesh.triangles_center[face1]
        point_b = self.mesh.triangles_center[face2]
        return np.linalg.norm(point_a - point_b)

    def observed_transition(self, face1, face2):
        # If the two faces are adjacent, mark the edge as observed, and we are done.
        if self.neighbor_graph.has_edge(face1, face2):
            self.walkable_graph.add_edge(face1, face2, type="observed")
            return

        # Visited surfaces.
        surf1 = self.origin_id[face1]
        surf2 = self.origin_id[face2]

        # If they belong to the same chunk, we can try to find a path among
        # adjacent faces that connects them and label that as walkable. This
        # is a bit risky, as it might cross obstacles. We could add some
        # intersection detection here to be more careful.
        if surf1 == surf2:
            try:
                path = nx.astar_path(self.neighbor_graph, face1, face2, heuristic=self.face_distance, weight=self.face_distance)
            except nx.NetworkXNoPath:
                return

            self.touched.update(path)
            for i in range(len(path) - 1):
                self.walkable_graph.add_edge(path[i], path[i+1], type="observed")

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

            self.walkable_graph.add_edge(exit1, exit2, type="boundary")

    def add_trace(self, times, points, apply_cylinder=False):
        """
        Annotate the mesh using a trace (user position history).

        This updates the set of visited faces and walkability information based
        on transitions observed in the trace.
        """
        down = np.array([0, -1, 0])

        print("trace has {} points".format(len(points)))
        directions = np.tile(down, [len(points), 1])

        locations, index_ray, index_tri = self.mesh.ray.intersects_location(ray_origins=points, ray_directions=directions, multiple_hits=False)
        self.visited.update(index_tri)

        # Even though the trace was in chronological order, for some reason
        # intersects_location returns them in a different order.
        sorted_rays = np.argsort(index_ray)
        print("intersections have {} points".format(len(sorted_rays)))

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
            surf1 = self.origin_id[face1]
            surf2 = self.origin_id[face2]

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
            # this is essentially the inner loop of trimesh.intersections.mesh_multiplane,
            # but their implementation includes some transformations that we do not need
            #
            # Also, the dot product is greatly simplified because we know we are intersecting
            # with horizontal planes. The dot product with the plane normal [0, 1, 0] simply
            # extracts the Y values from the vertices.
            new_origin = np.array([0, layer.height, 0])
            new_dots = self.mesh.vertices[:, 1] - layer.height

            walls = trimesh.intersections.mesh_plane(self.mesh, self.up, new_origin, cached_dots=new_dots)
            path = trimesh.load_path(walls)
            paths.append(path)

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

                for entity in path.entities:
                    if len(entity.points) == 2:
                        a, b = entity.points
                        line = dwg.line(start=path.vertices[a, [0, 2]], end=path.vertices[b, [0, 2]])
                    else:
                        line = dwg.polyline(points=[path.vertices[x, [0, 2]] for x in entity.points])
                    wall_group.add(line)

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

    def find_path(self, start, target):
        """
        Find a walkable path between two points.
        """
        i = self.find_face(start)
        j = self.find_face(target)

        if i is None:
            raise Exception("No face found below starting point")
        if j is None:
            raise Exception("No face found below target point")

        print("Searching for path from {} ({}) to {} ({})".format(start, i, target, j))

        def dist(a, b, *args):
            point_a = self.walkable_graph.nodes[a]['center']
            point_b = self.walkable_graph.nodes[b]['center']
            return np.linalg.norm(point_a - point_b)

        path = nx.astar_path(self.walkable_graph, i, j, heuristic=self.face_distance, weight=self.face_distance)

        vertices = []
        lines = []
        for x in path:
            vertices.append(self.walkable_graph.nodes[x]['center'])

        line = trimesh.path.entities.Line(list(range(len(vertices))), color=[255, 0, 0, 255])
        return trimesh.path.path.Path3D([line], np.array(vertices))

    def extract_surface_graph_paths(self):
        lines = []
        vertices = []

        for a, b in self.surface_graph.edges:
            line = trimesh.path.entities.Line([len(vertices), len(vertices)+1], color=[32, 0, 64, 255])
            lines.append(line)

            # Link between triangle u on surface a and triangle v on surface b.
            # Make a line between the centers of the two triangles.
            u, v = self.surface_graph.edges[a, b]['link']
            vertices.append(self.mesh.triangles_center[u])
            vertices.append(self.mesh.triangles_center[v])

        return trimesh.path.path.Path3D(lines, np.array(vertices))

    def extract_walkable_graph_paths(self):
        vertices = []
        for i in range(len(self.walkable_graph.nodes)):
            vertices.append(self.walkable_graph.nodes[i]['center'])

        lines = []
        for a, b in self.walkable_graph.edges:
            if self.walkable_graph.edges[a, b]['type'] == "observed":
                color = [0, 0, 255, 192]
            elif self.walkable_graph.edges[a, b]['type'] == "boundary":
                color = [128, 0, 128, 192]
            else:
                color = [0, 0, 128, 192]

            line = trimesh.path.entities.Line([a, b], color=color)
            lines.append(line)

        return trimesh.path.path.Path3D(lines, np.array(vertices))

    def extract_walkable_mesh(self):
        """
        Extract a submesh containing only walkable faces.

        This should be called after infer_walkable.

        Returns
            - submesh
            - list of lists, containing original face ids
        """
        subs = collections.defaultdict(list)
        for face in self.walkable:
            body = self.body_id[face]
            subs[body].append(face)

        subs_list = list(subs.values())
        mesh = self.mesh.submesh(subs_list)

        return mesh, subs_list

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

        meshes = []
        for fname in os.listdir(dir_path):
            path = os.path.join(dir_path, fname)
            mesh = trimesh.load(path)
            if isinstance(mesh, trimesh.Trimesh):
                meshes.append(mesh)

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

        soup.origin_id = np.array(origins)

        soup.mesh = trimesh.util.concatenate(meshes)
        soup.components, soup.body_id = cls.split_mesh(soup.mesh)

        soup.lower = np.min(soup.mesh.vertices, axis=0)
        soup.upper = np.max(soup.mesh.vertices, axis=0)

        for i in range(len(soup.mesh.faces)):
            soup.walkable_graph.add_node(i, center=soup.mesh.triangles_center[i])

        soup.neighbor_graph.add_edges_from(soup.mesh.face_adjacency)

        return soup
