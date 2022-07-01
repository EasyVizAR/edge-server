from .plyutil import read_ply_file


class ObjFileMaker:
    def __init__(self, surfaces, precision=3):
        self.surfaces = surfaces
        self.precision = precision

    def make_obj(self, output_path):
        with open(output_path, "w") as out:
            vertex_count = 0
            for surface in self.surfaces:
                vertex_count += self.write_surface(out, surface, voffset=vertex_count)

    def write_surface(self, out, surface, voffset=0):
        ply = read_ply_file(surface.filePath)

        if len(ply.vertices) == 0 or len(ply.triangles) == 0:
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
