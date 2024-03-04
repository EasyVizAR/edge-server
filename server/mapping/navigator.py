"""
This stub class is an example of how we can integrate navigation functionality
in the server. The server will create one instance of this class at startup,
and connect the on_headset_updated method to the event dispatcher so that it
fires whenever a headset is updated. This gives an opportunity to observe user
movements in real-time to update the map with passability information. Since
there is only one navigator instance for the server, we will need to use the
passed location_id to look up the appropriate map.
"""
import collections
import os
import time
import uuid

from server.resources.geometry import Vector3f

from .datagrid import DataGrid
from .floor import Floor


# Maximum time between consecutive user positions
MAXIMUM_TIME_DIFFERENCE = 5


def point_to_tuple(p):
    if isinstance(p, Vector3f):
        return p.totuple()
    elif isinstance(p, dict):
        return (p.get("x"), p.get("y"), p.get("z"))
    else:
        return p


class Navigator:
    def __init__(self, data_dir="."):
        self.data_dir = data_dir

        self.floors = dict()
        self.last_saved = collections.defaultdict(float)

    def find_path(self, location, layer, start, end):
        # Try to load a wall grid from one of the layers
        wall_grid = None
        if layer is not None:
            layer_dir = os.path.join(self.data_dir, 'locations', location.id.hex, 'layers', '{:08x}'.format(layer.id))
            npz_path = os.path.join(layer_dir, "walls.npz")
            if os.path.exists(npz_path):
                wall_grid = DataGrid.load(npz_path)

        floor_grid = self.get_floor_grid(location.id)

        stuple = start.totuple()
        etuple = end.totuple()

        # If we do not have walls or floors, we cannot navigate
        if wall_grid is None and floor_grid is None:
            return [start, end]

        elif wall_grid is None and floor_grid is not None:
            path = floor_grid.a_star(stuple, etuple, passable=DataGrid.ones_passable)

        elif wall_grid is not None and floor_grid is None:
            # Create an empty floor grid for this map
            # with the same shape as the wall grid
            floor_grid = DataGrid().resize_to_other(wall_grid)
            self.maybe_save_floor_grid(location.id, floor_grid)

            path = wall_grid.a_star(stuple, etuple, passable=DataGrid.zero_passable)

        else:
            # Expand the floor grid to match the latest wall grid
            floor_grid = floor_grid.resize_to_other(wall_grid)
            self.maybe_save_floor_grid(location.id, floor_grid)

            # Update the wall grid with information from the floor grid This
            # effectively cuts holes in the walls where we have observed user
            # paths (inferred doors).
            wall_grid.data -= floor_grid.data

            # Create a cost for unexplored cells. This lambda uses the
            # floor_grid to return 1.0 for unexplored cells and 0.0 for
            # explored cells.  This will be added to distances in the A* search
            # to bias the search in favor of explored cells.
            exploration_cost = lambda cell, value: 1.0 - floor_grid[cell]

            path = wall_grid.a_star(stuple, etuple, cost=exploration_cost, passable=DataGrid.zero_passable)

        if path is None:
            return [start, end]

        # Convert back to a path in three dimensions
        path3d = []
        for p in path:
            path3d.append(Vector3f(p[0], start.y, p[1]))

        return path3d

    def get_floor_grid(self, location_id):
        # Check in-memory cache first
        if location_id in self.floors:
            return self.floors[location_id]

        # Otherwise, try to load from file
        dname = os.path.join(self.data_dir, "navigator", location_id.hex)
        path = os.path.join(dname, "floor.npz")
        if os.path.exists(path):
            grid = DataGrid.load(path)
        else:
            grid = DataGrid(width=10.0, height=10.0, left=-5.0, top=-5.0)

        self.floors[location_id] = grid
        return grid

    def maybe_save_floor_grid(self, location_id, floor_grid, interval=15):
        """
        Save the floor grid if interval seconds have elapsed

        Setting interval to less than zero will force a save regardless of elapsed time.
        """
        # Set the cached grid
        self.floors[location_id] = floor_grid

        now = time.time()
        if now - self.last_saved[location_id] > interval:
            dname = os.path.join(self.data_dir, "navigator", location_id.hex)
            os.makedirs(dname, exist_ok=True)

            floor_grid.save_image(os.path.join(dname, "floor.png"))
            floor_grid.save(os.path.join(dname, "floor.npz"))
            self.last_saved[location_id] = now

    def add_trace(self, location, trace):
        floor_grid = self.get_floor_grid(location.id)

        layers = location.Layer.find(type="generated")

        # Try to load a wall grid from one of the layers
        wall_grid = None
        for layer in layers:
            if layer.type == "generated":
                npz_path = os.path.join(os.path.dirname(layer.imagePath), "walls.npz")
                if os.path.exists(npz_path):
                    wall_grid = DataGrid.load(npz_path)
                    break

        floor_grid = self.get_floor_grid(location.id)

        # If possible, resize floor grid to match wall grid.
        # We may have mapped the space but have a completely empty floor grid.
        if wall_grid is not None:
            floor_grid = floor_grid.resize_to_other(wall_grid)

        # Need to convert from list of dict to simple tuples
        points = []
        for point in trace:
            points.append(tuple(point['position'][k] for k in ['x', 'y', 'z']))

        for i in range(len(points) - 1):
            floor_grid.add_segment(points[i], points[i+1], vspread=1)

        self.maybe_save_floor_grid(location.id, floor_grid, interval=-1)

    async def on_headset_updated(self, event, uri, *args, **kwargs):
        current = kwargs.get('current')
        previous = kwargs.get('previous')

        # server/headset/models: describes the Headset class that the code is receiving

        if current['location_id'] is None:
            return

        if current['position'] is None or previous['position'] is None:
            return

        if current['type'] not in ['phone', 'headset']:
            return

        # If the time difference is too long, we cannot safely infer that
        # the line between the two points is passable
        if current['updated'] - previous['updated'] > MAXIMUM_TIME_DIFFERENCE:
            return

        location_id = uuid.UUID(current['location_id'])
        if location_id not in self.floors:
            self.floors[location_id] = DataGrid(width=10.0, height=10.0, left=-5.0, top=-5.0)

        floor_grid = self.get_floor_grid(location_id)

        # TODO: Change to have multiple floors in a single location and differentiate between each using y position
        floor_grid.add_segment(point_to_tuple(previous['position']), point_to_tuple(current['position']), vspread=1)

        self.maybe_save_floor_grid(location_id, floor_grid)

        # TODO: Change to put line in floor
        #floor.put_line([(previous.position.x, previous.position.z),
        #                (current.position.x, current.position.z)])
        #floor.user_locations.write_png("heatmap-{}.png".format(current.location_id))

        #print("Headset in location {} moved from {} to {}".format(
        #    current.location_id, previous.position, current.position))

        # current.position.x, current.position.z

        # TODO: use the old and new position to mark passable cells in the map
