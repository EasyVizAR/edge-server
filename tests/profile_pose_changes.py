"""
Generate a large number of artificial pose changes and measure performance of
the CsvCollection methods, particularly 'find'.

python3 -m tests.profile_pose_changes.py
"""

import cProfile

from server.pose_changes.models import PoseChangeModel
from server.resources.csvresource import CsvCollection


num_iterations = 10000


if __name__ == "__main__":
    PoseChange = CsvCollection(PoseChangeModel, "pose-change")
    PoseChange.clear()

    for i in range(num_iterations):
        item = PoseChange()
        PoseChange.add(item)

    print("=== PoseChange.find() ===")
    cProfile.run("PoseChange.find()")

    PoseChange.clear()
