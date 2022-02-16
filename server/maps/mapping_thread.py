import os
import shutil
import tempfile
import threading

from server.mapping.floorplanner import Floorplanner


class MappingThread(threading.Thread):
    def __init__(self, map_obj, map_dir):
        super().__init__()
        self.dirty = threading.Event()
        self.running = True
        self.map_obj = map_obj
        self.map_dir = map_dir

    def notify(self):
        self.dirty.set()

    def run(self):
        ply_files = os.path.join(self.map_dir, 'surfaces', '*.ply')
        json_file = os.path.join(self.map_dir, 'floor-plan.json')
        floorplanner = Floorplanner(ply_files, json_data_path=json_file)

        image_path = os.path.join(self.map_dir, 'floor-plan.svg')

        while self.running:
            self.dirty.wait()
            self.dirty.clear()

            changes = floorplanner.update_lines(initialize=False)
            if changes > 0:
                # We will write to a temporary file, then atomically replace
                # the destination file. This should place nicely, if someone
                # is trying to read the image at the same time.
                temp_fd, temp_path = tempfile.mkstemp()
                os.close(temp_fd)

                view_box = floorplanner.write_image(temp_path)

                self.map_obj.image = 'floor-plan.svg'
                self.map_obj.viewBox = view_box
                self.map_obj.save()

                # Use shutil.move instead of os.replace because the file may
                # cross filesystems.
                shutil.move(temp_path, image_path)
