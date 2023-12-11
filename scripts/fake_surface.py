"""
This script generates a random wall surface and sends it to the server to
trigger a map change.
"""

import os
import random
import sys
import time
import uuid

import requests


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")

ply_data = """ply
format ascii 1.0
comment System: unity
element vertex 4
property double x
property double y
property double z
property double nx
property double ny
property double nz
element face 2
property list uchar int vertex_index
end_header
1.0 1.0 {z} 0.0 0.0 -1.0
-1.0 1.0 {z} 0.0 0.0 -1.0
-1.0 -1.0 {z} 0.0 0.0 -1.0
1.0 -1.0 {z} 0.0 0.0 -1.0
3 0 1 2
3 2 3 0
"""


def upload_surface(location_id):
    surface_id = uuid.uuid4()

    z = 2.0 * random.random() - 1.0
    surface_data = ply_data.format(z=z)

    url = "{}/locations/{}/surfaces/{}/surface.ply".format(SERVER_URL, location_id, surface_id)
    requests.put(url, data=surface_data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <location-id>".format(sys.argv[0]))
        sys.exit(1)

    location_id = sys.argv[1]

    upload_surface(location_id)

