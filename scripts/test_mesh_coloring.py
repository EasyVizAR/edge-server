# Set PYGLET_HEADLESS=1 in the environment if running headless.

import os

import numpy as np
import quaternion
import requests

from pprint import pprint

from server.mapping2.scene import LayerConfig, LocationModel


model = LocationModel.from_obj("data/locations/acf9cc39a7a84ea4bc108959cae35582/model.obj")
#model = LocationModel.from_directory("data/locations/acf9cc39a7a84ea4bc108959cae35582/surfaces")

res = requests.get("https://easyvizar.wings.cs.wisc.edu/photos?camera_location_id=acf9cc39-a7a8-4ea4-bc10-8959cae35582")
photos = res.json()

for i, photo in enumerate(photos):
    print("Photo {} / {}".format(i, len(photos)))
    pos = photo['camera_position']
    if isinstance(pos, dict):
        pos = np.array([pos['x'], pos['y'], pos['z']])

    rot = photo['camera_orientation']
    if isinstance(rot, dict):
        rot = quaternion.as_rotation_matrix(np.quaternion(rot['w'], rot['x'], rot['y'], rot['z']))

    path = "data/locations/acf9cc39a7a84ea4bc108959cae35582/photos/{:08x}/photo.png".format(photo['id'])

    try:
        model.apply_color(path, (700, 700), pos, rot, focal_relative=False)
    except Exception as error:
        print(error)

layers = [LayerConfig(svg_output="test.svg")]
model.infer_walls(layers)

model.save("test.pickle")
model.export_obj("test.obj")

model.show()
