import os

from .plyutil import read_ply_file

from server.incidents.models import Incident


class ObjFileMaker:
    def __init__(self, surfaces, output_path, precision=3):
        self.surfaces = surfaces
        self.output_path = output_path
        self.precision = precision

    def make_obj(self):
        with open(self.output_path, "w") as out:
            vertex_count = 0
            for surface in self.surfaces:
                vertex_count += self.write_surface(out, surface, voffset=vertex_count)

    def write_surface(self, out, surface, voffset=0):
        ply = read_ply_file(surface.filePath)

        if ply is None or len(ply.vertices) == 0 or len(ply.triangles) == 0:
            return 0

        # The OBJ file format supports group/object designations, but the
        # interpretation is up to the loading application.  Unity seems to use
        # the group line, while Blender seems to use the object line.
        out.write("g {} {}\n".format(surface.label, surface.id))
        out.write("o {}\n".format(surface.id))

        vertex_line = "v {{:0.0{0}f}} {{:0.0{0}f}} {{:0.0{0}f}}\n".format(self.precision)
        for v in ply.vertices:
            out.write(vertex_line.format(v[0], v[1], v[2]))

        for f in ply.triangles:
            out.write("f {} {} {}\n".format(f[0]+voffset+1, f[1]+voffset+1, f[2]+voffset+1))

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
