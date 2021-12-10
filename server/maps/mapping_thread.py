import os
import shutil
import tempfile
import threading

from server.mapping.floorplanner import Floorplanner


class MappingThread(threading.Thread):
    def __init__(self, map_dir):
        super().__init__()
        self.dirty = threading.Event()
        self.running = True
        self.map_dir = map_dir

    def notify(self):
        self.dirty.set()

    def run(self):
        ply_files = os.path.join(self.map_dir, 'surfaces', '*.ply')
        json_file = os.path.join(self.map_dir, 'top-down.json')
        floorplanner = Floorplanner(ply_files, json_file)

        image_path = os.path.join(self.map_dir, 'top-down.svg')

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

                floorplanner.write_image(temp_path)

                # Use shutil.move instead of os.replace because the file may
                # cross filesystems.
                shutil.move(temp_path, image_path)
