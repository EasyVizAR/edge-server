from .plyutil import read_ply_file


class ObjFileMaker:
    def __init__(self, surfaces, precision=3):
        self.surfaces = surfaces
        self.precision = precision

    def make_obj(self, output_path):
        surface_data = dict()
        vertex_count = 0
        for surface in self.surfaces:
            ply = read_ply_file(surface.filePath)
            surface_data[surface.id] = {
                "vertices": ply.vertices,
                "faces": ply.triangles,
                "voffset": vertex_count + 1
            }
            vertex_count += len(ply.vertices)

        with open(output_path, "w") as out:
            self.write_header(out, surface_data)
            self.write_vertices(out, surface_data)
            self.write_faces(out, surface_data)

    def write_header(self, out, surface_data):
        for surface in self.surfaces:
            data = surface_data[surface.id]
            out.write("# Surface {}, updated {}, by {}\n".format(surface.id, surface.updated, surface.uploadedBy))

    def write_vertices(self, out, surface_data):
        vertex_line = "v {{:0.0{0}f}} {{:0.0{0}f}} {{:0.0{0}f}}\n".format(self.precision)
        for surface in self.surfaces:
            out.write("# Vertices for surface {}\n".format(surface.id))

            data = surface_data[surface.id]
            for v in data['vertices']:
                out.write(vertex_line.format(v[0], v[1], v[2]))

    def write_faces(self, out, surface_data):
        for surface in self.surfaces:
            out.write("# Faces for surface {}\n".format(surface.id))

            data = surface_data[surface.id]
            voffset = data['voffset']
            for f in data['faces']:
                out.write("f {} {} {}\n".format(f[0]+voffset, f[1]+voffset, f[2]+voffset))
