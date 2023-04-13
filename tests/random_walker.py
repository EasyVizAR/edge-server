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


def get_headset(headset_id):
    url = "{}/headsets/{}".format(SERVER_URL, headset_id)
    res = requests.get(url)
    if res.ok:
        return res.json()
    else:
        print("Querying for headset failed with code: {}".format(res.status_code))
        sys.exit(1)


def move_headset(headset_id, position):
    url = "{}/headsets/{}".format(SERVER_URL, headset_id)
    data = {
        "position": position
    }
    res = requests.patch(url, json=data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <headset-id>".format(sys.argv[0]))
        sys.exit(1)

    headset_id = sys.argv[1]

    headset = get_headset(headset_id)

    print("Headset Name: {}".format(headset['name']))
    print("Location ID: {}".format(headset['location_id']))
    print("Headset Page: {}/#/headsets/{}".format(SERVER_URL, headset_id))
    print("Sending position updates...")

    position = headset['position']
    while True:
        position['x'] += random.gauss(0, 0.1)
        position['z'] += random.gauss(0, 0.1)

        move_headset(headset_id, position)

        time.sleep(0.2)
