import tempfile

from server.mapping.datagrid import DataGrid


def test_get_and_set():
    grid = DataGrid(width=10, height=10, left=-5, top=-5)

    k = grid.xyz_to_index((0, 0, 0))

    grid[k] = 42
    assert grid[k] == 42
    assert grid[(0, 0, 0)] == 42


def test_add_segment():
    grid = DataGrid(width=10, height=10, left=-5, top=-5)

    # horizontal line through origin
    grid.add_segment((0,0,0), (100,0,0))

    assert grid[(0,0,0)] > 0.5
    assert grid[(0,0,5)] < 0.5


def test_a_star():
    # Construct a realistic scenario where we have a horizontal wall from the
    # left and stopping at the origin. Then we find a shortcut, which is a door,
    # that allows us to go directly from a point in the top left to bottom left
    # point.
    #
    # |-----------|
    # |           |
    # | a         |
    # | .         |
    # | .         |
    # | .         |
    # |#.####     |
    # | .         |
    # | .         |
    # | .         |
    # | b         |
    # |           |
    # |-----------|
    wall = DataGrid(width=10, height=10, left=-5, top=-5)

    # horizontal line from left, stopping at the origin
    wall.add_segment((-6,0,0), (0,0,0))

    # Find a path from the top left to bottom left of map.
    # The path must be at least 3 points because we need to
    # go around the wall.
    path = wall.a_star((-4, 0, -4), (-4, 0, 4), passable=DataGrid.zero_passable)
    assert len(path) > 2

    # Now set up an empty floor map and add a trace directly
    # from point a to b.
    floor = DataGrid().resize_to_other(wall)
    floor.add_segment((-4, 0, -4), (-4, 0, 4), vspread=1)

    # Navigation on the floor map should produce a direct path
    # with only two points.
    path = floor.a_star((-4, 0, -4), (-4, 0, 4), passable=DataGrid.ones_passable)
    assert len(path) == 2

    # Now combine walls and floors, which cuts a whole through the wall.
    test = DataGrid().resize_to_other(wall)
    test.data = wall.data - floor.data

    # This should still find a direct path.
    path = test.a_star((-4, 0, -4), (-4, 0, 4), passable=DataGrid.zero_passable)
    assert len(path) == 2


def test_contains():
    grid = DataGrid(width=10, height=10, left=-5, top=-5)

    # Tuple bounds testing
    assert (0, 0) in grid
    assert (grid.H-1, grid.W-1) in grid

    assert (grid.H, grid.W) not in grid
    assert (-1, -1) not in grid

    # Point bounds testing
    assert [0, 0, 0] in grid
    assert [4, 0, 4] in grid
    assert [-4, 0, -4] in grid

    assert [6, 0, 6] not in grid
    assert [-6, 0, -6] not in grid


def test_save_and_load():
    grid = DataGrid(width=10, height=10, left=-5, top=-5)
    k = grid.xyz_to_index((0, 0, 0))

    grid[k] = 42
    assert grid[k] == 42

    fp = tempfile.TemporaryFile()
    grid.save(fp)

    fp.seek(0)
    other = DataGrid.load(fp)

    assert other.H == grid.H
    assert other.W == grid.W
    assert other[k] == 42


def test_resize_to_other():
    grid = DataGrid(width=10, height=10, left=-5, top=-5)

    k0 = grid.xyz_to_index((0, 0, 0))
    k1 = grid.xyz_to_index((1, 2, 3))
    k2 = grid.xyz_to_index((-1.1, 0.0, 1.1))
    grid[k0] = 42
    grid[k1] = 24
    grid[k2] = 100

    same = grid.resize_to_other(grid)
    assert same.H == grid.H
    assert same.W == grid.W
    assert same[k0] == 42
    assert same[k1] == 24
    assert same[k2] == 100

    large = DataGrid(width=20, height=20, left=-5, top=-5)
    grow = grid.resize_to_other(large)
    assert grow.H > grid.H
    assert grow.W > grid.W
    assert grow[(0, 0, 0)] == 42
    assert grow[(1, 2, 3)] == 24
    assert grow[(-1.1, 0.0, 1.1)] == 100

    small = DataGrid(width=5, height=5, left=-2.5, top=-2.5)
    shrink = grow.resize_to_other(small)
    assert shrink.H < grid.H
    assert shrink.W < grid.W
    assert shrink[(0, 0, 0)] == 42
    # We lose the value for (1, 2, 3) because it is out of bounds now
    assert shrink[(-1.1, 0.0, 1.1)] == 100

    test = shrink.resize_to_other(grid)
    assert test.H == grid.H
    assert test.W == grid.W
    assert test[k0] == 42
    assert test[k1] == 0
    assert test[k2] == 100

    # Make sure after growing and shrinking operations, we consistently associate
    # the same grid cell with the origin coordinate.
    point = test.index_to_xz(k0)
    assert abs(point[0] - 0.0) < 0.01
    assert abs(point[1] - 0.0) < 0.01

    # Likewise with point 1
    point = test.index_to_xz(k1)
    assert abs(point[0] - 1.0) < 0.01
    assert abs(point[1] - 3.0) < 0.01

    # And point 2
    original = grid.index_to_xz(k2)
    point = test.index_to_xz(k2)
    assert abs(point[0] - original[0]) < 0.01
    assert abs(point[1] - original[1]) < 0.01
