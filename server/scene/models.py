import time

from server.resources.dataclasses import dataclass, field
from server.resources.dictresource import DictResource


# SceneDescriptor is not stored on disk but is created whenever a client
# interacts with the scene API. It is simply intended to give useful
# information, particularly the URL path to the scene JSON file.

@dataclass
class SceneDescriptor:
    headset_id: str = field(default=None,
                            description="Headset ID that submitted the scene file")

    file_url: str = field(default=None,
                          description="Path on the server to the scene file, e.g. /locations/x/scenes/y.json")

    modified: float = field(default_factory=time.time,
                            description="Last modified time of the scene file (seconds since Unix epoch)")


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
