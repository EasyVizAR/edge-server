"""
This script forces a rebuild of a location map by fetching and uploading
a surface mesh.
"""


import os
import random
import sys
import time

import requests


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


def get_surfaces(location_id):
    url = "{}/locations/{}/surfaces".format(SERVER_URL, location_id)
    res = requests.get(url)
    if res.ok:
        return res.json()
    else:
        print("Querying for surfaces failed with code: {}".format(res.status_code))
        sys.exit(1)


def fetch_and_resend_surface(location_id, surface_id):
    url = "{}/locations/{}/surfaces/{}/surface.ply".format(SERVER_URL, location_id, surface_id)
    res = requests.get(url)
    if res.ok:
        requests.put(url, data=res.text)
    else:
        print("Querying for surface failed with code: {}".format(res.status_code))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <location-id>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]

    surfaces = get_surfaces(location_id)
    if len(surfaces) > 0:
        surface_id = surfaces[0]['id']
        print("Fetch and resend surface {}".format(surface_id))
        fetch_and_resend_surface(location_id, surface_id)
    else:
        print("Location has no surfaces")
