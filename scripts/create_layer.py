"""
This script creates a new map layer.
"""


import os
import random
import sys
import time

import requests


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


def create_layer(location_id, name="unknown", type="generated", content_type="image/svg+xml"):
    url = "{}/locations/{}/layers".format(SERVER_URL, location_id)
    data = {
        "contentType": content_type,
        "name": name,
        "type": type,
        "viewBox": {
            "height": 1.0,
            "width": 1.0,
            "left": -0.5,
            "top": -0.5
        }
    }
    res = requests.post(url, json=data)
    if res.ok:
        return res.json()
    else:
        print("Creating layer failed with code: {}".format(res.status_code))
        sys.exit(1)


def upload_layer_image(location_id, layer_id, path):
    url = "{}/locations/{}/layers/{}/image".format(SERVER_URL, location_id, layer_id)
    with open(path, "rb") as source:
        data = source.read()
    res = requests.put(url, data=data)
    if res.ok:
        return res.json()
    else:
        print("Uploading layer image failed with code: {}".format(res.status_code))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: {} <location id> <layer name> <layer type> <image path>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]
    layer_name = sys.argv[2]
    layer_type = sys.argv[3]
    image_path = sys.argv[4]

    layer = create_layer(location_id, name=layer_name, type=layer_type)
    upload_layer_image(location_id, layer['id'], image_path)
