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
        self.total_incidents = 0
        self.set_current_incident()

    def set_current_incident(self):
        filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')
        incident_num = -1
        num_incidents = 0

        os.makedirs(filepath, exist_ok=True)
        for folder in os.scandir(filepath):
            # If there is at least one incident, set the current incident
            # number to the highest valued one.
            if folder.is_dir():
                num_incidents += 1
                if int(folder.name) > incident_num:
                    incident_num = int(folder.name)

        self.current_incident = incident_num
        self.total_incidents = num_incidents

        # Only create a new incident if none exist.
        if incident_num == -1:
            self.create_new_incident()

        print("Current incident: {}".format(self.current_incident))

    def create_new_incident(self, incident_name=None):
        self.total_incidents += 1
        self.current_incident = self.total_incidents

        # create filepaths
        filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents', str(self.total_incidents))
        new_headset_filepath = os.path.join(filepath, 'headsets')
        new_map_filepath = os.path.join(filepath, 'maps')

        # create the directories
        os.makedirs(filepath, exist_ok=True)
        os.makedirs(new_headset_filepath, exist_ok=True)
        os.makedirs(new_map_filepath, exist_ok=True)

        if not incident_name:
            incident_name = ''

        # create incident info file
        filepath = os.path.join(filepath, 'incident_info.json')
        incident_info = {
            'name': incident_name,
            'created': str(date.today())
        }

        write_to_file(json.dumps(incident_info, cls=GenericJsonEncoder), filepath)

    def get_all_incident_info(self):
        past_incident_info = []
        base_filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')

        for folder in os.scandir(base_filepath):
            if folder.is_dir():
                incident_info_filepath = os.path.join(base_filepath, folder.name, 'incident_info.json')
                try:
                    info = open(incident_info_filepath)
                    data = json.load(info)
                    info.close()
                except FileNotFoundError:
                    # At least for now, it should not be a problem if the file does not exist.
                    data = {}

                data['incident_number'] = folder.name

                past_incident_info.append(data)

        return past_incident_info

    def get_incident_name(self, incident_number):
        if int(incident_number) > self.current_incident or int(incident_number) < 0:
            return None

        base_filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')

        for folder in os.scandir(base_filepath):
            if folder.is_dir() and folder.name == str(incident_number):
                incident_info_filepath = os.path.join(base_filepath, folder.name, 'incident_info.json')
                try:
                    info = open(incident_info_filepath)
                    data = json.load(info)
                    info.close()

                    return data.get('name')

                except FileNotFoundError:
                    # At least for now, it should not be a problem if the file does not exist.
                    return None
        return None

    def update_inident_name(self, incident_number, new_name):
        if int(incident_number) > self.current_incident or int(incident_number) < 0:
            return False

        if new_name is None:
            new_name = ''

        base_filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')

        for folder in os.scandir(base_filepath):
            if folder.is_dir() and folder.name == str(incident_number):
                incident_info_filepath = os.path.join(base_filepath, folder.name, 'incident_info.json')
                try:
                    info = open(incident_info_filepath)
                    data = json.load(info)
                    info.close()

                    data['name'] = new_name
                    write_to_file(json.dumps(data, cls=GenericJsonEncoder), incident_info_filepath)

                except FileNotFoundError:
                    # At least for now, it should not be a problem if the file does not exist.
                    return False
        return True

    def delete_incident(self, incident_number):
        if int(incident_number) > self.current_incident or int(incident_number) < 0:
            return False

        base_filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')

        for folder in os.scandir(base_filepath):
            if folder.is_dir() and folder.name == str(incident_number):
                try:
                    shutil.rmtree(os.path.join(base_filepath, folder.name))
                    self.set_current_incident()

                except FileNotFoundError:
                    # At least for now, it should not be a problem if the file does not exist.
                    return False
        return True

    def restore_incident(self, new_incident):
        print('start of restore incident')
        if int(new_incident) < 0:
            return False

        base_filepath = os.path.join(self.app.config['VIZAR_DATA_DIR'], 'incidents')
        print('new incident ' + str(new_incident))
        for folder in os.scandir(base_filepath):
            print('looking at ' + folder.name)
            if folder.is_dir() and folder.name == str(new_incident):
                print('returned')
                self.current_incident = int(new_incident)
                return True

        return False


def init_incidents_handler(app=None):
    global incidents_handler

    if app is None:
        app = current_app

    if incidents_handler is None:
        incidents_handler = IncidentHandler(app)

    return incidents_handler
