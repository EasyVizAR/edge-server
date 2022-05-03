import collections
import os
import queue
import shutil
import tempfile
import threading
import traceback

from server.incidents.models import Incident
from server.mapping.floorplanner import Floorplanner


class MappingThread(threading.Thread):
    def __init__(self):
        # Setting daemon=True allows the server to exit without waiting for
        # this worker thread to finish. As written, the worker thread would
        # never exit. This is somewhat risky because the mapping thread could
        # be terminated in the middle of processing a map update.
        super().__init__(daemon=True)

        self.running = True
        self.work_queue = queue.Queue()

    def enqueue_task(self, incident_id):
        item = incident_id
        self.work_queue.put(item, block=False)

    def process_task(self, incident_id):
        incident = Incident.find_by_id(incident_id)
        surfaces = incident.Surface.find()

        files_by_location = collections.defaultdict(list)
        for surface in surfaces:
            files_by_location[surface.locationId].append(surface.filePath)

        for location_id, files in files_by_location.items():
            # If location_id is None, we are not really sure what building this
            # surface came from. Making assumptions is OK for now, but we need
            # the headsets to be aware of the location_id when they send
            # surfaces.
            if location_id is None:
                location = incident.Location.find_newest()
            else:
                location = incident.Location.find_by_id(location_id)

            layers = location.Layer.find(type="generated")
            if len(layers) == 0:
                layer = location.Layer(id=None, name="Division 0", type="generated", contentType="image/svg+xml")
                layer.contentType = "image/svg+xml"
                layer.imageUrl = "/locations/{}/layers/{}/image".format(location.id, layer.id)
                layer.save()
            else:
                layer = layers[0]

            layer.imagePath = os.path.join(layer.get_dir(), "floor_plan.svg")
            json_file = os.path.join(layer.get_dir(), "floor_plan.json")
            floorplanner = Floorplanner(files, json_data_path=json_file)

            changes = floorplanner.update_lines(initialize=False)
            if changes > 0:
                layer.viewBox = floorplanner.write_image(layer.imagePath)
                layer.ready = True
                layer.save()

    def run(self):
        while self.running:
            incident_id = self.work_queue.get()

            try:
                self.process_task(incident_id)
            except Exception as e:
                print("Error in mapping thread: {}".format(e))
                traceback.print_tb(e.__traceback__)

            self.work_queue.task_done()
