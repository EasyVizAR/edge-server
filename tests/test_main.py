def test_import_app_object():
    """
    Make sure app object can be imported without error.
    """
    from server.main import app
    assert app is not None
