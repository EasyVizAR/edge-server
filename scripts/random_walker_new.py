"""
This script generates random movements for a headset which can be used to test
visualizations and other code that depends on headsets moving. It may also be
useful for stress-testing and profiling server code.
"""


import os
import random
import sys
import time

import requests


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


def register_headset(location_id):
    url = f"{SERVER_URL}/headsets"
    data = {
        "name": "Random Walker",
        "location_id": location_id
    }
    res = requests.post(url, json=data)
    if res.ok:
        return res.json()
    else:
        print("Register headset failed with code: {}".format(res.status_code))
        sys.exit(1)


def move_headset(headset, position, orientation):
    url = f"{SERVER_URL}/headsets/{headset['id']}"
    headers = {
        "Authorization": f"Bearer {headset['token']}"
    }
    data = {
        "position": position,
        "orientation": orientation,
    }
    res = requests.patch(url, headers=headers, json=data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <location-id>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]

    headset = register_headset(location_id)

    print("Headset Name: {}".format(headset['name']))
    print("Location ID: {}".format(headset['location_id']))
    print("Headset Page: {}/#/headsets/{}".format(SERVER_URL, headset['id']))
    print("Sending position updates...")

    position = {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    }
    orientation = {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "w": 1.0,
    }
    while True:
        position['x'] += random.gauss(0, 0.1)
        position['z'] += random.gauss(0, 0.1)

        # This is not going to produce a valid quaternion...
        orientation['x'] += random.gauss(0, 0.1)
        orientation['y'] += random.gauss(0, 0.1)
        orientation['z'] += random.gauss(0, 0.1)
        orientation['w'] += random.gauss(0, 0.1)

        move_headset(headset, position, orientation)

        time.sleep(0.2)
