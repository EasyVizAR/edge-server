# Set PYGLET_HEADLESS=1 in the environment if running headless.

import os

import numpy as np
import quaternion

from pprint import pprint

from server.mapping2.scene import LayerConfig, LocationModel


model = LocationModel.from_obj("data/locations/acf9cc39a7a84ea4bc108959cae35582/model.obj")
#model = LocationModel.from_directory("data/locations/acf9cc39a7a84ea4bc108959cae35582/surfaces")

position = np.array([-1.7503215074539185, 0.9768016934394836, 0.8648117780685425])
orientation = quaternion.as_rotation_matrix(np.quaternion(-0.49627333879470825, -0.06341710686683655, -0.8560729026794434, 0.12973228096961975))

model.apply_color("data/locations/acf9cc39a7a84ea4bc108959cae35582/photos/00002190/photo.png", (700, 700), position, orientation)

layers = [LayerConfig(svg_output="test.svg")]
model.infer_walls(layers)

model.export_obj("test.obj")

model.show()
