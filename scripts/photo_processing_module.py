"""
This script shows an example of how to implement a photo processing module that
fetches photos from the edge API server, performs some kind of processing such
as object detection, and sends the results back. This script shows how to
upload a new annotated image and how to place markers that will be visible to
AR users.
"""

import operator
import os
import time

from http import HTTPStatus

import requests


QUEUE_NAME = os.environ.get("QUEUE_NAME", "detection-3d")
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")
WAIT_TIMEOUT = os.environ.get("WAIT_TIMEOUT", 30)

MIN_RETRY_INTERVAL = 5

MARKER_HEIGHT = 1


def main():
    while True:
        start_time = time.time()

        query_url = f"{SERVER_URL}/photos?queue_name={QUEUE_NAME}&wait={WAIT_TIMEOUT}"
        items = []
        try:
            response = requests.get(query_url)
            if response.ok and response.status_code == HTTPStatus.OK:
                items = response.json()
        except requests.exceptions.RequestException as error:
            # Most common case is if the API server is restarting,
            # then we see a connection error temporarily.
            print(error)

        print(f"Query returned {len(items)} items.")

        # Check if the empty/error response from the server was sooner than
        # expected.  If so, add an extra delay to avoid spamming the server.
        # We need this in case long-polling is not working as expected.
        if len(items) == 0:
            elapsed = time.time() - start_time
            if elapsed < MIN_RETRY_INTERVAL:
                time.sleep(MIN_RETRY_INTERVAL - elapsed)
            continue

        for item in items:
            # Sort by priority level (descending), then creation time (ascending)
            item['priority_tuple'] = (-1 * item.get("priority", 0), item.get("created"))

        items.sort(key=operator.itemgetter("priority_tuple"))
        for item in items:
            # Photo base URL using photo ID
            photo_url = f"{SERVER_URL}/photos/{item['id']}"

            # URL to fetch image file
            image_url = f"{photo_url}/image"
            print(image_url)

            # RUN DETECTOR HERE

            # Send any updates to the server, including moving
            # the photo into the "done" queue.
            update = {
                "status": "done"
            }
            requests.patch(photo_url, json=update)

            # If the detector outputs an annotated image with labels and/or
            # bounding boxes, we can send that to the server to be displayed on
            # the dashboard.
            annotated3d_url = f"{photo_url}/annotated3d.png"
            print(annotated3d_url)
            headers = {
                "Content-Type": "image/png"
            }
            #req = requests.put(annotated3d_url, data=image_data, headers=headers)

            # Camera extrinsic information
            camera_position = item.get("camera_position")
            camera_orientation = item.get("camera_orientation")
            location_id = item.get("camera_location_id")

            # If camera location is not known, then we are unable to place a marker.
            if None in [camera_position, camera_orientation, location_id]:
                continue

            newly_detected_objects = [ "dummy object for illustration purposes" ]
            for obj in newly_detected_objects:
                # Create a map marker at the location of the detected object.
                #
                # X and Z are the horizontal axes and should be set to the center
                # of the object, perhaps. Y is the vertical axis and should be set
                # high enough to be above the object.
                #
                # The name will be visible to AR users, so it should be set to
                # the object label or something equally meaningful.
                marker = {
                    "name": "chair",
                    "position": {
                        "x": camera_position['x'],
                        "y": MARKER_HEIGHT,
                        "z": camera_position['z']
                    },
                    "type": "object"
                }
                marker_url = f"{SERVER_URL}/locations/{location_id}/features"
                requests.post(marker_url, json=marker)


if __name__ == "__main__":
    main()
