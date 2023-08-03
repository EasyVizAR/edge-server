"""
"""


import os
import random
import sys
import time

import requests

import numpy as np
from PIL import Image

from server.mapping.navgrid import NavigationGrid


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


def get_layers(location_id):
    url = "{}/locations/{}/layers".format(SERVER_URL, location_id)
    res = requests.get(url)
    if res.ok:
        return res.json()
    else:
        print("GET {} failed with code {}".format(url, res.status_code))
        sys.exit(1)


def get_headsets():
    url = "{}/headsets".format(SERVER_URL)
    res = requests.get(url)
    if res.ok:
        return res.json()
    else:
        print("GET {} failed with code {}".format(url, res.status_code))
        sys.exit(1)


def get_check_ins(headset_id, location_id):
    url = "{}/headsets/{}/check-ins?location_id={}".format(SERVER_URL, headset_id, location_id)
    res = requests.get(url)
    if res.ok:
        return res.json()
    else:
        print("GET {} failed with code {}".format(url, res.status_code))
        sys.exit(1)


def get_pose_changes(headset_id, check_in_id):
    url = "{}/headsets/{}/check-ins/{}/pose-changes".format(SERVER_URL, headset_id, check_in_id)
    res = requests.get(url)
    if res.ok:
        return res.json()
    else:
        print("GET {} failed with code {}".format(url, res.status_code))
        sys.exit(1)


def walk_traces(location_id, handler, delay=0.2):
    headsets = get_headsets()

    for headset in headsets:
        if delay > 0:
            time.sleep(delay)

        headset['check-ins'] = get_check_ins(headset['id'], location_id)
        headset['check-ins'].sort(key=lambda x: int(x['id']))

        for check_in in headset['check-ins']:
            print("Fetching headset {} check-in {}".format(headset['id'], check_in['id']))
            pose_changes = get_pose_changes(headset['id'], check_in['id'])
            if len(pose_changes) > 1:
                handler(pose_changes)
            if delay > 0:
                time.sleep(delay)

    return headsets


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <location-id>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]

    geometry = None
    layers = get_layers(location_id)
    for layer in layers:
        if layer['type'] == "generated":
            geometry = layer['viewBox']
            break
    print("geometry: {}".format(geometry))

    grid = NavigationGrid(geometry=geometry)
    print(grid)

    walk_traces(location_id, grid.add_trace)
    grid.save_image("grid.png")

    print("Finding path:")
    path = grid.a_star([0, 0, 0], [51.875, 0, -8.042])
    for p in path:
        print(p)
