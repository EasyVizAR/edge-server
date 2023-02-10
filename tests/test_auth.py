from server.auth import Authenticator


def test_authenticator():
    auth = Authenticator()
    token = auth.create_headset_token("0000")
    assert len(token) > 0
    assert token in auth.headsets
