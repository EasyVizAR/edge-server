from server.headset.models import HeadsetModel, Headset


def test_headset_model():
    item = HeadsetModel("0")
    assert item.id == "0"
    assert len(item.name) > 0
    assert item.created > 0
    assert item.updated > 0
    assert int(item.position.x) == 0
    assert int(item.position.y) == 0
    assert int(item.position.z) == 0
    assert int(item.orientation.x) == 0
    assert int(item.orientation.y) == 0
    assert int(item.orientation.z) == 0
    assert item.matches({}) is True
    assert item.matches({"name": item.name}) is True
    assert item.matches({"name": ""}) is False


def test_headset_collection():
    headsets = Headset.find()
    assert isinstance(headsets, list)

    item = Headset(None, name="Test")
    item.save()

    assert item.id is not None
    assert item.name == "Test"
    assert item.created > 0
    assert item.updated > 0

    results = Headset.find(id=item.id)
    assert len(results) == 1

    result = Headset.find_by_id(item.id)
    assert result is not None

    item.delete()
