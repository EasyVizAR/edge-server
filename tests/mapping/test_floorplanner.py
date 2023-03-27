from server.mapping.floorplanner import Floorplanner


def test_floorplanner():
    fp = Floorplanner([])
    assert 'files' in fp.data
    assert 'cutting_height' in fp.data

    fp.update_lines(initialize=True)
    assert 'files' in fp.data
    assert 'cutting_height' in fp.data

    fp.update_lines(initialize=False)
    assert 'files' in fp.data
    assert 'cutting_height' in fp.data
