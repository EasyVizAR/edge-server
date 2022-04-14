from server.pose_changes.models import PoseChangeModel


def test_pose_change_model():
    item = PoseChangeModel()
    assert item.time > 0
    assert int(item.position.x) == 0
    assert int(item.position.y) == 0
    assert int(item.position.z) == 0
    assert int(item.orientation.x) == 0
    assert int(item.orientation.y) == 0
    assert int(item.orientation.z) == 0
    assert item.matches({}) is True
    assert item.matches({"time": "-1"}) is False
