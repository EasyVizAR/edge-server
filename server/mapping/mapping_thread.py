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

    def enqueue_task(self, incident_id, location_id):
        item = (incident_id, location_id)
        self.work_queue.put(item, block=False)

    def process_task(self, incident_id, location_id):
        incident = Incident.find_by_id(incident_id)
        location = incident.Location.find_by_id(location_id)
        surfaces = location.Surface.find()

        surface_files = [surface.filePath for surface in surfaces]

        layers = location.Layer.find(type="generated")
        if len(layers) == 0:
            layer = location.Layer(id=None, name="Division 0", type="generated", contentType="image/svg+xml")
            layer.contentType = "image/svg+xml"
            layer.imageUrl = "/locations/{}/layers/{}/image".format(location.id, layer.id)
            layer.save()
        else:
            # TODO: different layers for the floors of a building
            layer = layers[0]

        layer.imagePath = os.path.join(layer.get_dir(), "floor_plan.svg")
        json_file = os.path.join(layer.get_dir(), "floor_plan.json")
        floorplanner = Floorplanner(surface_files, json_data_path=json_file)

        changes = floorplanner.update_lines(initialize=False)
        if changes > 0:
            layer.viewBox = floorplanner.write_image(layer.imagePath)
            layer.ready = True
            layer.save()

    def run(self):
        while self.running:
            incident_id, location_id = self.work_queue.get()

            try:
                self.process_task(incident_id, location_id)
            except Exception as e:
                print("Error in mapping thread: {}".format(e))
                traceback.print_tb(e.__traceback__)

            self.work_queue.task_done()
