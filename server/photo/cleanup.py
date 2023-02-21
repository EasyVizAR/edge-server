import time

from server.incidents.models import Incident


# Time to retain "temporary" photos (seconds)
temporary_photo_retention = 300


class PhotoCleanupTask:
    def __init__(self, incident_id):
        self.incident_id = incident_id

    def run(self):
        incident = Incident.find_by_id(self.incident_id)
        photos = incident.Photo.find()

        now = time.time()

        photos_removed = 0
        for photo in photos:
            if photo.retention == "temporary" and (now - photo.created) >= temporary_photo_retention:
                photo.delete()
                photos_removed += 1

        print("PhotoCleanupTask removed {} photos from incident {}".format(photos_removed, self.incident_id))
