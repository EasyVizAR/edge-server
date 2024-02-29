"""
This script creates a new map layer.
"""


import os
import random
import sys
import time

import requests


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


def create_photo_queue(name, next_queue, display_order, description):
    url = "{}/photos/queues".format(SERVER_URL)
    data = {
        "name": name,
        "next_queue_name": next_queue,
        "display_order": display_order,
        "description": description
    }
    res = requests.post(url, json=data)
    if res.ok:
        return res.json()
    else:
        print("Creating layer failed with code: {}".format(res.status_code))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: {} <name> <next queue name> <display order> <description>".format(sys.argv[0]))
        sys.exit(1)

    create_photo_queue(*sys.argv[1:])
