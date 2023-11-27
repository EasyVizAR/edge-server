import os

from quart import g

import sqlalchemy as sa

from .plyutil import read_ply_file

from server.models.surfaces import Surface
from server.incidents.models import Incident


class ObjFileMaker:
    def __init__(self, surfaces, output_path, surface_dir, precision=3):
        self.surfaces = surfaces
        self.output_path = output_path
        self.surface_dir = surface_dir
        self.precision = precision

    def make_obj(self):
        with open(self.output_path, "w") as out:
            vertex_count = 0
            for surface in self.surfaces:
                vertex_count += self.write_surface(out, surface, voffset=vertex_count)

    def write_surface(self, out, surface, voffset=0):
        source_path = os.path.join(self.surface_dir, "{}.ply".format(surface.id.hex))

        ply = read_ply_file(source_path)
        if ply is None or len(ply.vertices) == 0 or len(ply.triangles) == 0:
            return 0

        # The OBJ file format specifies a right-handed coordinate system.
        # Data loaded from Unity will be left-handed. Unity also uses the
        # convention of negating X when loading an OBJ file, so we will
        # do the same here.
        x_mult = 1
        if ply.extra.get("system") == "unity":
            x_mult = -1

        label = surface.mobile_device_id
        if label is None:
            label = "unknown"

        # The OBJ file format supports group/object designations, but the
        # interpretation is up to the loading application.  Unity seems to use
        # the group line, while Blender seems to use the object line.
        out.write("g {} {}\n".format(label, surface.id))
        out.write("o {}\n".format(surface.id))

        vertex_line = "v {{:0.0{0}f}} {{:0.0{0}f}} {{:0.0{0}f}}\n".format(self.precision)
        for v in ply.vertices:
            out.write(vertex_line.format(x_mult * v[0], v[1], v[2]))

        normal_line = "vn {{:0.0{0}f}} {{:0.0{0}f}} {{:0.0{0}f}}\n".format(self.precision)
        for n in ply.normals:
            out.write(normal_line.format(x_mult * n[0], n[1], n[2]))

        if x_mult > 0:
            for f in ply.triangles:
                out.write("f {0}//{0} {1}//{1} {2}//{2}\n".format(f[0]+voffset+1, f[1]+voffset+1, f[2]+voffset+1))
        else:
            # For reversing handedness, we also need to reverse the winding
            # order of the triangles.
            for f in reversed(ply.triangles):
                out.write("f {2}//{2} {1}//{1} {0}//{0}\n".format(f[0]+voffset+1, f[1]+voffset+1, f[2]+voffset+1))

        return len(ply.vertices)

    @classmethod
    def build_maker(cls, incident_id, location_id):
        """
        Build an ObjFileMaker instance.

        This should be called from the main thread.
        """
        incident = Incident.find_by_id(incident_id)
        location = incident.Location.find_by_id(location_id)
        surfaces = location.Surface.find()

        output_path = os.path.join(location.get_dir(), "model.obj")

        return ObjFileMaker(surfaces, output_path)

    @classmethod
    async def build_maker_from_db(cls, location_id):
        stmt = sa.select(Surface) \
                .where(Surface.location_id == location_id)

        result = await g.session.execute(stmt)
        surfaces = result.scalars().all()

        location_dir = os.path.join(g.data_dir, "locations", location_id.hex)
        surface_dir = os.path.join(location_dir, "surfaces")
        output_path = os.path.join(location_dir, "model.obj")

        return ObjFileMaker(surfaces, output_path, surface_dir)
