from server.mapping.grid import Grid


def test_grid_put_line():
    grid = Grid(5)

    a = (0, 0)
    b = (1, 0)

    grid.put_line([a, b])

    assert a in grid
    assert b in grid

    minv, maxv = grid.get_ranges()
    assert minv[0] == 0
    assert minv[1] == 0
    assert maxv[0] == 5
    assert maxv[1] == 0
