from server.resources.dataclasses import field


def test_dataclasses_field():
    x = field(default=None)
    assert x.default is None

    y = field(default=None, description="foo")
    assert y.default is None
    assert y.metadata['metadata']['description'] == "foo"
