import os
import pickle
import time
import uuid

from pathlib import Path
from urllib.request import urlopen

import numpy as np
import svgwrite
import trimesh

from PIL import Image

DISPLAY = os.environ.get("DISPLAY")


hand_change_transform = np.diag([-1, 1, 1, 1])


class LayerConfig:
    def __init__(self, height=0, svg_output=None):
        self.height = height
        self.svg_output = svg_output


def normalized_uuid(x):
    try:
        return uuid.UUID(x)
    except:
        return x


class MeshColorSource():
    def __init__(self, image_path, focal, position, rotation, focal_relative=True):
        self.image_path = image_path
        self.focal = focal
        self.position = position
        self.rotation = rotation
        self.focal_relative = focal_relative

    def __eq__(self, other):
        return self.image_path == other.image_path

    def __hash__(self):
        return hash(self.image_path)

    def __repr__(self):
        return "MeshColorSource({})".format(self.image_path)

    def generate_rays(self, right_handed=False):
        if self.image_path.startswith("http"):
            image = Image.open(urlopen(self.image_path))
        else:
            image = Image.open(self.image_path)
        image = np.array(image)

        position = self.position
        rotation = self.rotation
        if right_handed:
            position = position * [-1, 1, 1]
            rotation = np.matmul(hand_change_transform[0:3, 0:3], rotation)

        fx, fy = self.focal
        if self.focal_relative:
            fx *= image.shape[1]
            fy *= image.shape[0]
        cx = 0.5 * image.shape[1]
        cy = 0.5 * image.shape[0]

        directions = np.ones((image.shape[0] * image.shape[1], 3))
        i = 0
        for y in range(image.shape[0]):
            for x in range(image.shape[1]):
                directions[i, 0] = (x - cx) / fx
                directions[i, 1] = (cy - y) / fy
                i += 1

        # Rotate the direction vectors according to camera orientation.
        directions = np.matmul(directions, rotation.T)

        # The origin for each array is the camera position, so just repeat it N times.
        origins = np.repeat(position[np.newaxis, :], directions.shape[0], axis=0)

        colors = image[:, :, 0:3].reshape(-1, 3)

        return origins, directions, colors


class LocationModel():
    up = np.array([0, 1, 0])
    down = np.array([0, -1, 0])

    surface_pruning_threshold = 0.6

    def __init__(self):
        self.scene = trimesh.Scene()
        self.combined_mesh = trimesh.Trimesh()
        self.face_object_indices = np.array([], dtype=int)
        self.face_local_indices = np.array([], dtype=int)
        self.surface_ids = []

        self.right_handed = True

        self.color_sources = set()

        self.mtime = time.time()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['combined_mesh']
        # TODO del any fields we do not want saved
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        meshes = []
        for i, obj in enumerate(self.scene.dump()):
            meshes.append(obj)

        self.combined_mesh = trimesh.util.concatenate(meshes)
        # TODO recalculate any fields that were not saved

    def apply_color(self, image_path, focal, position, rotation, focal_relative=True):
        color_source = MeshColorSource(image_path, focal, position, rotation, focal_relative)
        self.apply_color_source(color_source)

    def apply_color_source(self, color_source, should_reapply=False):
        # Avoid redoing an image unless requested to reapply
        if not should_reapply and color_source in self.color_sources:
            return

        self.color_sources.add(color_source)

        try:
            origins, directions, colors = color_source.generate_rays(self.right_handed)
        except:
            return

        # Ray cast against the environment mesh.
        points, index_ray, index_tri = self.combined_mesh.ray.intersects_location(origins, directions, multiple_hits=False)
        if len(points) == 0:
            return

        # Hit triangle vertices and color for each ray.
        hit_triangle_vertices = np.zeros((len(index_ray), 3, 3))
        ray_colors = np.zeros((len(index_ray), 3))

        # For each ray, find the triangle that was hit in the combined mesh.
        # Record the triangle vertices and pixel color.
        for i, ray in enumerate(index_ray):
            tri = index_tri[i]
            global_face_vertices = self.combined_mesh.faces[tri]
            hit_triangle_vertices[i, 0:3, 0:3] = self.combined_mesh.vertices[global_face_vertices, :]
            ray_colors[i, 0:3] = colors[ray, 0:3]

        # Accumulators for color and weight contributions from each ray.
        acc_color = np.zeros((len(self.combined_mesh.vertices), 3))
        acc_weight = np.zeros(len(self.combined_mesh.vertices))

        # Compute barycentric coordinates for each ray's collision point.
        barycentric = trimesh.triangles.points_to_barycentric(hit_triangle_vertices, points)

        for d in range(3):
            weighted_color = barycentric[:, [d]] * ray_colors

            for i, tri in enumerate(index_tri):
                acc_color[self.combined_mesh.faces[tri][d], 0:3] += weighted_color[i, :]
                acc_weight[self.combined_mesh.faces[tri][d]] += barycentric[i, d]

        surface_index = 0
        surface_id = self.surface_ids[surface_index]
        submesh = self.scene.geometry[str(surface_id)]
        local_vertex_index = 0

        # Iterate over the vertices in the combined mesh, map them back to the
        # scene mesh, and apply color to the scene mesh.
        for i in range(acc_color.shape[0]):
            if local_vertex_index >= len(submesh.vertices):
                surface_index += 1
                surface_id = self.surface_ids[surface_index]
                submesh = self.scene.geometry[str(surface_id)]
                local_vertex_index = 0

            # Color vertices where we had at least one hit and avoid small divisor.
            if acc_weight[i] > 0.33:
                submesh.visual.vertex_colors[local_vertex_index][0:3] = acc_color[i] / acc_weight[i]

                # Maintain a set of MeshColorSource objects that affected each surface.
                # Then, when a surface is replaced, we can reapply only the images that should affect it.
                submesh.metadata['color_sources'].add(color_source)

            local_vertex_index += 1

    def compute_max_iou(self, mesh):
        """
        Compute intersection-over-union (IOU) between given mesh and existing
        mesh with maximal overlap.

        Returns (max IOU, mesh name)
        """
        N = len(self.scene.geometry)
        if N == 0:
            return 0, None

        # Extract the upper and lower bounds for all of our current meshes
        # TODO: these arrays could be cached if it is determined to save time
        lower_bounds = np.zeros((N, 3))
        upper_bounds = np.zeros((N, 3))
        volume = np.zeros((N, ))
        names = list()
        for i, obj in enumerate(self.scene.dump()):
            bbox = obj.bounding_box
            lower_bounds[i, :] = bbox.bounds[0, :]
            upper_bounds[i, :] = bbox.bounds[1, :]
            volume[i] = bbox.volume
            names.append(obj.metadata['name'])

        # Find the intersection with the given mesh
        given_bbox = mesh.bounding_box
        inter_lower = np.maximum(given_bbox.bounds[0, :], lower_bounds)
        inter_upper = np.minimum(given_bbox.bounds[1, :], upper_bounds)

        inter_volume = np.product(inter_upper - inter_lower, axis=1)

        # If the upper bound ended up less than the lower bound in any
        # dimension, it means there is no overlap, so the intersection volume
        # is zero in those cases.
        inter_volume[np.any(inter_upper < inter_lower, axis=1)] = 0

        union_volume = given_bbox.volume + volume - inter_volume
        iou = inter_volume / union_volume

        i = np.argmax(iou)
        return iou[i], names[i]

    def export_obj(self, path, include_color=False):
        # For OBJ file format, right handed coordinate system is expected.
        # Default is using RH in trimesh, so no change would be needed to import/export.
        if self.right_handed:
            scene = self.scene
        else:
            scene = self.scene.copy()
            scene.apply_transform(hand_change_transform)

        scene.export(file_obj=path, file_type="obj", digits=3, include_color=include_color, include_normals=False, include_texture=False)

    def get_bounding_box(self):
        lower = np.min(self.combined_mesh.vertices, axis=0)
        upper = np.max(self.combined_mesh.vertices, axis=0)
        size = upper - lower

        if self.right_handed:
            left = -1 * upper[0]
        else:
            left = lower[0]

        dims = {
            "left": left,
            "top": lower[2],
            "width": size[0],
            "height": size[2]
        }
        return dims

    def has_color(self):
        return len(self.color_sources) > 0

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

            walls = trimesh.intersections.mesh_plane(self.combined_mesh, self.up, origin, cached_dots=dots)
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
                if self.right_handed:
                    x_scale = -1
                    x_offset = lower[0] + upper[0]
                else:
                    x_scale = 1
                    x_offset = 0
                transform_group = dwg.g(id="transform", transform="matrix({} 0 0 -1 {} {})".format(x_scale, x_offset, lower[2] + upper[2]))
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

    def load_surface(self, path):
        fname = os.path.basename(path)
        surface_id, ext = os.path.splitext(fname)
        surface_id = normalized_uuid(surface_id)

        surface = trimesh.load(path)
        if isinstance(surface, trimesh.Trimesh) and len(surface.faces) > 0:
            if self.right_handed and ext == ".ply":
                # Assume PLY files are provided in Unity (left-handed) coordinate system.
                # Convert to RH coordinates.
                surface.apply_transform(hand_change_transform)
                trimesh.repair.fix_winding(surface)

            surface.metadata['color_sources'] = set()

            # Set the mesh name to be the surface ID.
            # This will be preserved if the mesh is exported as OBJ.
            surface.metadata['name'] = str(surface_id)

            # Save the mtime of the surface PLY file, so we can detect updated files.
            surface.metadata['mtime'] = os.path.getmtime(path)

            return surface, surface_id

        return None, surface_id

    def append_surface(self, surface):
        """
        Add a new surface.

        This does not check if the surface already existed and modifies the
        called Scene object.
        """
        self.scene.add_geometry(surface)

        surface_id = normalized_uuid(surface.metadata['name'])
        self.surface_ids.append(surface_id)

        foi = np.array([len(self.surface_ids)-1] * len(surface.faces), dtype=int)
        self.face_object_indices = np.concatenate((self.face_object_indices, foi))

        fli = np.array(range(len(surface.faces)), dtype=int)
        self.face_local_indices = np.concatenate((self.face_local_indices, fli))

        self.combined_mesh = trimesh.util.concatenate(self.combined_mesh, surface)

    def replace_surface(self, surface_id, surface):
        """
        Replace or add a surface.

        Note: this can be used to replace a mesh with surface ID differing from
        the new surface, ie. remove mesh X and append mesh Y.
        """
        used_color_sources = set()

        surface_id = normalized_uuid(surface_id)
        key = str(surface_id)

        if key in self.scene.geometry:
            used_color_sources = self.scene.geometry[key].metadata['color_sources']
            self.scene.delete_geometry(key)

        self.scene.add_geometry(surface)

        surface_ids = []
        face_object_indices = []
        face_local_indices = []
        meshes = []

        for i, obj in enumerate(self.scene.dump()):
            surface_ids.append(obj.metadata['name'])
            face_object_indices.extend([i] * len(obj.faces))
            face_local_indices.extend(list(range(len(obj.faces))))
            meshes.append(obj)

        self.combined_mesh = trimesh.util.concatenate(meshes)
        self.surface_ids = surface_ids
        self.face_object_indices = np.array(face_object_indices, dtype=int)
        self.face_local_indices = np.array(face_local_indices, dtype=int)

        return used_color_sources

    def save(self, path):
        """
        Save the current scene to a pickle file.

        Loading from a pickle should be faster than parsing OBJ or PLY files.
        """
        with open(path, "wb") as output:
            pickle.dump(self, output)

    def show(self):
        scene = self.scene.copy()

        if self.right_handed:
            world_axis = trimesh.creation.axis(origin_size=0.2, transform=hand_change_transform)
        else:
            world_axis = trimesh.creation.axis(origin_size=0.2)
        scene.add_geometry(world_axis)

        print(scene)
        print("Right handed: {}".format(self.right_handed))

        lower = np.min(self.combined_mesh.vertices, axis=0)
        upper = np.max(self.combined_mesh.vertices, axis=0)
        print("Bounds: {} to {}".format(lower, upper))

        print("Cameras:")
        for source in self.color_sources:
            cam = np.eye(4)
            cam[0:3, 0:3] = source.rotation
            cam[0:3, 3] = source.position
            if self.right_handed:
                cam = np.matmul(hand_change_transform, cam)
            cam_axis = trimesh.creation.axis(origin_size=0.1, transform=cam, origin_color=[0, 0, 255, 255])
            scene.add_geometry(cam_axis)
            print("  Camera {}".format(source.position))

        if DISPLAY is None:
            print("No display, rendering to test.png instead.")
            png = scene.save_image()
            with open("test.png", "wb") as output:
                output.write(png)
        else:
            scene.show()

    def update_from_directory(self, dir_path):
        """
        Update the scene from files in a directory taking only those surfaces
        files which are new or have been modified.
        """
        print("Update from directory: {}".format(dir_path))
        if isinstance(dir_path, str):
            path = Path(dir_path)

        used_color_sources = set()
        updated_model_mtime = self.mtime
        for path in sorted(path.iterdir(), key=os.path.getmtime, reverse=True):
            fname = os.path.basename(path)
            surface_id, ext = os.path.splitext(fname)
            surface_id = normalized_uuid(surface_id)

            mtime = os.path.getmtime(path)
            existing_surface = self.scene.geometry.get(str(surface_id))

            # Skip any surface files older than the model itself.
            # They are either already included or meant to be excluded.
            if mtime < self.mtime:
                break

            # Save the newest surface mtime for later.
            elif mtime > updated_model_mtime:
                updated_model_mtime = mtime

            # Detect new surfaces and append.
            # If no change, there is no need to load and parse the mesh file.
            if existing_surface is None:
                surface, _ = self.load_surface(path)

                iou, overlapping_surface_id = self.compute_max_iou(surface)
                if iou < self.surface_pruning_threshold:
                    print("Surface {} is new".format(surface_id))
                    self.append_surface(surface)
                else:
                    overlapping_surface = self.scene.geometry[overlapping_surface_id]
                    if mtime > overlapping_surface.metadata['mtime']:
                        # TODO: we might actually want to find all existing, older surfaces
                        # with IOU > threshold and replace them all
                        print("Surface {} replaces {}".format(surface_id, overlapping_surface_id))
                        used_color_sources = self.replace_surface(overlapping_surface_id, surface)
                    else:
                        print("Surface {} is redundant".format(surface_id))

            # Detect modified surfaces and replace
            elif mtime > existing_surface.metadata['mtime']:
                print("Surface {} is modified".format(surface_id))

                surface, _ = self.load_surface(path)
                used_color_sources = self.replace_surface(surface_id, surface)

        # Update the model modified time to exclude all processed surfaces in future updates.
        self.mtime = updated_model_mtime

        if len(used_color_sources) > 0:
            print("Change requires {} color sources be reapplied".format(len(used_color_sources)))
            for source in used_color_sources:
                self.apply_color_source(source, should_reapply=True)

    @classmethod
    def from_directory(cls, dir_path):
        """
        Load scene from a directory containing PLY files.
        """
        model = LocationModel()

        if isinstance(dir_path, str):
            path = Path(dir_path)

        for path in sorted(path.iterdir(), key=os.path.getmtime, reverse=True):
            surface, surface_id = model.load_surface(path)
            if surface is not None:
                iou, _ = model.compute_max_iou(surface)
                if iou < cls.surface_pruning_threshold:
                    model.append_surface(surface)

        return model

    @classmethod
    def from_obj(cls, obj_path):
        """
        Load scene from an OBJ file.
        """
        model = LocationModel()
        loaded_scene = trimesh.load(obj_path, group_material=False)

        # Get the mtime of the OBJ file, which is an upper bound on
        # the modified times for the component surfaces.
        model.mtime = os.path.getmtime(obj_path)

        for item in loaded_scene.dump():
            if isinstance(item, trimesh.Trimesh) and len(item.faces) > 0:
                if not model.right_handed:
                    # Meshes are loaded in RH coordinate system.
                    item.apply_transform(hand_change_transform)
                    trimesh.repair.fix_winding(item)

                item.metadata['color_sources'] = set()

                # We do not have the individual surface mtimes, but the OBJ file
                # mtime will suffice.
                item.metadata['mtime'] = model.mtime

                model.append_surface(item)

        return model

    @classmethod
    def from_pickle(cls, pickle_path):
        """
        Load scene from a pickle file.
        """
        with open(pickle_path, "rb") as source:
            scene = pickle.load(source)
        return scene
