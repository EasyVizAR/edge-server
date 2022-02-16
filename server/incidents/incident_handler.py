import os
import shutil
from datetime import date
import json

from quart import current_app

from server.utils.utils import write_to_file, GenericJsonEncoder

incidents_handler = None


class IncidentHandler:
    def __init__(self, app):
        self.current_incident = 0
        self.app = app
        self.set_current_incident()

    def set_current_incident(self):
        filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')
        incident_num = -1

        os.makedirs(filepath, exist_ok=True)
        for folder in os.scandir(filepath):
            # If there is at least one incident, set the current incident
            # number to the highest valued one.
            if folder.is_dir() and int(folder.name) > incident_num:
                incident_num = int(folder.name)

        self.current_incident = incident_num

        # Only create a new incident if none exist.
        if incident_num == -1:
            self.create_new_incident()

        print("Current incident: {}".format(self.current_incident))

    def create_new_incident(self):
        self.current_incident += 1

        # create filepaths
        filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents', str(self.current_incident))
        new_headset_filepath = os.path.join(filepath, 'headsets')
        new_map_filepath = os.path.join(filepath, 'maps')

        # create the directories
        os.makedirs(filepath, exist_ok=True)
        os.makedirs(new_headset_filepath, exist_ok=True)
        os.makedirs(new_map_filepath, exist_ok=True)

        # create incident info file
        filepath = os.path.join(filepath, 'incident_info.json')
        incident_info = {
            'created': str(date.today())
        }

        write_to_file(json.dumps(incident_info, cls=GenericJsonEncoder), filepath)

    def create_first_incident(self):

        # create filepaths
        filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents', str(self.current_incident))
        new_headset_filepath = os.path.join(filepath, 'headsets')
        new_map_filepath = os.path.join(filepath, 'maps')

        # create the directories
        os.makedirs(filepath, exist_ok=True)
        os.makedirs(new_headset_filepath, exist_ok=True)
        os.makedirs(new_map_filepath, exist_ok=True)

        # create incident info file
        filepath = os.path.join(filepath, 'incident_info.json')
        incident_info = {
            'created': str(date.today())
        }

        write_to_file(json.dumps(incident_info, cls=GenericJsonEncoder), filepath)


def init_incidents_handler(app=None):
    global incidents_handler

    if app is None:
        app = current_app

    if incidents_handler is None:
        incidents_handler = IncidentHandler(app)

    return incidents_handler
