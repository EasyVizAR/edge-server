import os
import pickle

from pathlib import Path

import numpy as np
import svgwrite
import trimesh


class LayerConfig:
    def __init__(self, height=0, svg_output=None):
        self.height = height
        self.svg_output = svg_output


class Scene(trimesh.Scene):
    up = np.array([0, 1, 0])
    down = np.array([0, -1, 0])

    def __init__(self):
        super().__init__()
        self.combined_mesh = trimesh.Trimesh()
        self.face_object_indices = np.array([], dtype=int)
        self.face_local_indices = np.array([], dtype=int)
        self.surface_ids = []

    def __getstate__(self):
        state = self.__dict__.copy()
        # TODO del any fields we do not want saved
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # TODO recalculate any fields that were not saved

    def apply_color(self, photo):
        # TODO make sure camera position is valid
        # TODO load image

        resolution = [480, 640]
        center = photo.camera_position.as_array()
        rot_mat = photo.camera_orientation.as_rotation_matrix()
        fx, fy, cx, cy = photo.camera.relative_parameters()

        pixel_coords = []
        directions = []
        for y in range(height):
            for x in range(width):
                pixel_coords.append((y, x))
                direction = np.array([
                    ((x / width) - cx) / fx,
                    (cy - (y / height)) / fy,
                    1
                ])

                # Multiply by the camera rotation matrix to produce
                # direction vector in world coordinate frame.
                direction = np.matmul(rot_mat, direction)
                directions.append(direction)

        origins = [np.array(center)] * len(directions)

        # Ray cast against the environment mesh.
        points, index_ray, index_tri = self.combined_mesh.ray.intersects_location(origins, directions, multiple_hits=False)
        if len(points) == 0:
            return

        for i, ray in enumerate(index_ray):
            y, x = pixel_coords[ray]
            tri = index_tri[i]
            surface_index = self.face_object_indices[tri]
            surface_id = self.surface_ids[surface_index]
            local_face_index = self.face_local_indices[tri]
            # TODO add color to the hit triangle in the scene

    def export_obj(self, path):
        # Negate x-axis to convert handedness. Unity-based OBJ loader are
        # expected to reverse this operation.
        transform = np.eye(4)
        transform[0, 0] = -1
        self.apply_transform(transform)

        self.export(file_obj=path, file_type="obj", digits=3, include_color=False, include_normals=False, include_texture=False)

    def infer_walls(self, layers):
        lower = np.min(self.combined_mesh.vertices, axis=0)
        upper = np.max(self.combined_mesh.vertices, axis=0)

        paths = []
        for i, layer in enumerate(layers):
            # this is essentially the inner loop of trimesh.intersections.mesh_multiplane,
            # but their implementation includes some transformations that we do not need
            #
            # Also, the dot product is greatly simplified because we know we are intersecting
            # with horizontal planes. The dot product with the plane normal [0, 1, 0] simply
            # extracts the Y values from the vertices.
            origin = np.array([0, layer.height, 0])
            dots = self.combined_mesh.vertices[:, 1] - layer.height

            walls = trimesh.intersections.mesh_plane(self.combined_mesh, Scene.up, origin, cached_dots=dots)
            path = trimesh.load_path(walls)
            paths.append(path)

            if layer.svg_output is not None:
                size = upper - lower
                viewBox="{} {} {} {}".format(lower[0], lower[2], size[0], size[2])

                dwg = svgwrite.Drawing(layer.svg_output, profile='tiny', viewBox=viewBox)

                # This transformation flips the image vertically to account for the
                # fact that SVG uses the convention that the image starts at the top
                # left corner with increasing coordinates down and to the right.
                # The vertical axis ends up being the opposite of our mapping system.
                transform_group = dwg.g(id="transform", transform="matrix(1 0 0 -1 0 {})".format(lower[2] + upper[2]))
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

    def append_surface(self, surface_id, surface):
        """
        Add a new surface.

        This does not check if the surface already existed and modifies the
        called Scene object.
        """
        self.add_geometry(surface)
        self.surface_ids.append(surface_id)

        foi = np.array([len(self.surface_ids)-1] * len(surface.faces), dtype=int)
        self.face_object_indices = np.concatenate((self.face_object_indices, foi))

        fli = np.array(range(len(surface.faces)), dtype=int)
        self.face_local_indices = np.concatenate((self.face_local_indices, fli))

        self.combined_mesh = trimesh.util.concatenate(self.combined_mesh, surface)

    def replace_surface(self, surface_id, surface):
        """
        Replace or add a surface.

        Returns a new Scene object with the surface added.
        """
        scene = Scene()

        found = False
        face_object_indices = []
        face_local_indices = []
        meshes = []

        surface.metadata['name'] = surface_id

        for i, obj in enumerate(self.dump()):
            if self.surface_ids[i] == surface_id:
                # Replace the old version of this surface.
                scene.add_geometry(surface)
                scene.surface_ids.append(self.surface_ids[i])
                face_object_indices.extend([i] * len(surface.faces))
                face_local_indices.extend(list(range(len(surface.faces))))
                meshes.append(surface)
                found = True

            else:
                # Keep any unchanged surfaces.
                scene.add_geometry(obj)
                scene.surface_ids.append(surface_id)
                face_object_indices.extend([i] * len(obj.faces))
                face_local_indices.extend(list(range(len(obj.faces))))
                meshes.append(obj)

        if not found:
            # This is a new surface we have not scene before.
            scene.add_geometry(surface)
            scene.surface_ids.append(surface_id)
            face_object_indices.extend([len(meshes)] * len(surface.faces))
            face_local_indices.extend(list(range(len(surface.faces))))
            meshes.append(surface)

        scene.combined_mesh = trimesh.util.concatenate(meshes)
        scene.face_object_indices = np.array(face_object_indices, dtype=int)
        scene.face_local_indices = np.array(face_local_indices, dtype=int)
        return scene

    def save(self, path):
        """
        Save the current scene to a pickle file.

        Loading from a pickle should be faster than parsing OBJ or PLY files.
        """
        with open(path, "wb") as output:
            pickle.dump(self, output)

    @classmethod
    def from_directory(cls, dir_path):
        scene = Scene()

        if isinstance(dir_path, str):
            path = Path(dir_path)

        for path in sorted(path.iterdir(), key=os.path.getmtime, reverse=True):
            fname = os.path.basename(path)
            surface_id, ext = os.path.splitext(fname)

            surface = trimesh.load(path)
            if isinstance(surface, trimesh.Trimesh):
                # TODO we were using IOU to detect redundant meshes, maybe reimplement that
                scene.append_surface(surface_id, surface)

        return scene
