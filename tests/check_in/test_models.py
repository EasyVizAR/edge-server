from server.check_in.models import CheckInModel


def test_check_in_model():
    item = CheckInModel(0)
    assert item.start_time > 0
