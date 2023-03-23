from server.resources.geometry import Vector3f
from server.utils import patch


class MockHeadset:
    def __init__(self):
        self.name = "Mock"
        self.position = Vector3f()


def test_patch_by_path():
    headset = MockHeadset()

    patch.patch_by_path(headset, ["name"], "Test2")
    assert headset.name == "Test2"

    patch.patch_by_path(headset, ["position", "x"], 1)
    assert headset.position.x == 1
    assert headset.position.y == 0
    assert headset.position.z == 0


def test_patch_object():
    headset = MockHeadset()

    patch.patch_object(headset, {"name": "Test2"})
    assert headset.name == "Test2"

    # Selectively set position.x
    patch.patch_object(headset, {"position.x": 1})
    assert headset.position.x == 1
    assert headset.position.y == 0
    assert headset.position.z == 0

    # Selectively set position.y but through a nested dictionary.
    patch.patch_object(headset, {"position": {"y": 2}})
    assert headset.position.x == 1
    assert headset.position.y == 2
    assert headset.position.z == 0
