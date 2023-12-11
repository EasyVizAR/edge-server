import uuid

from server.auth import Authenticator


def test_authenticator():
    device_id = uuid.uuid4()

    auth = Authenticator()
    token = auth.create_temporary_token(device_id)
    assert len(token) > 0

    assert token in auth.cache
