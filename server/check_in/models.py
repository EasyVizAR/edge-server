import time

from server.resources.csvresource import CsvCollection
from server.resources.dataclasses import dataclass, field
from server.resources.jsonresource import JsonResource

from server.pose_changes.models import PoseChangeModel


@dataclass
class CheckInModel(JsonResource):
    """
    Record of a headset check-in. This is the first time the headset scans a QR
    code and makes its presence at a location known to us.

    Headsets can report a location check-in by sending a POST request to this
    endpoint, but the server also automatically creates a check-in record under
    certain circumstances. Whenever a headset first sets its current
    location_id, we will create a check-in. Also, if a headset changes its
    location_id in a PUT or PATCH operation, we will create a check-in.
    """
    id: int

    start_time:     float = field(default_factory=time.time,
                                  description="Starting time of the check-in (seconds since Unix epoch)")
    location_id:    str = field(default=None,
                                description="Location ID")

    def on_ready(self):
        self.PoseChange = CsvCollection(PoseChangeModel, "pose-change", parent=self)
