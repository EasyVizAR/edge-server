from dataclasses import field
from marshmallow_dataclass import dataclass

from server.resources.dictresource import DictResource


@dataclass
class SceneModel(DictResource):
    """
    A scene is a simplified representation of the environment with 3D models
    for walls, floors, and other surfaces. It is the result of scanning with a
    single headset using scene understanding and is meant for easy rendering in
    Unity.

    The scene is transferred and stored as a JSON file with no server-side
    validation of schema. There may be one scene file for each headset x
    location pair.
    """
    id: str = field(default=None)
