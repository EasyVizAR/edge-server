"""
This stub class is an example of how we can integrate navigation functionality
in the server. The server will create one instance of this class at startup,
and connect the on_headset_updated method to the event dispatcher so that it
fires whenever a headset is updated. This gives an opportunity to observe user
movements in real-time to update the map with passability information. Since
there is only one navigator instance for the server, we will need to use the
passed location_id to look up the appropriate map.
"""
import os
import time

from server.location.models import LocationModel
from server.resources.geometry import Vector3f

from .datagrid import DataGrid
from .floor import Floor


# Seconds between saving explored floor maps
SAVE_INTERVAL = 15

# Maximum time between consecutive user positions
MAXIMUM_TIME_DIFFERENCE = 5


class Navigator:
    def __init__(self):
        self.floors = {}
        self.last_saved = 0

    def find_path(self, location: LocationModel, start, end):
        layers = location.Layer.find(type="generated")
        # from server/location/models

        # Try to load a wall grid from one of the layers
        wall_grid = None
        for layer in layers:
            if layer.type == "generated":
                npz_path = os.path.join(os.path.dirname(layer.imagePath), "walls.npz")
                if os.path.exists(npz_path):
                    wall_grid = DataGrid.load(npz_path)
                    break

        floor_grid = self.floors.get(location.id)

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
            self.floors[location.id] = DataGrid().resize_to_other(wall_grid)

            path = wall_grid.a_star(stuple, etuple, passable=DataGrid.zero_passable)

        else:
            # Expand the floor grid to match the latest wall grid
            floor_grid = floor_grid.resize_to_other(wall_grid)
            self.floors[location.id] = floor_grid

            # Create a temporary combined floor and wall grid
            nav_grid = DataGrid().resize_to_other(wall_grid)
            nav_grid.data = wall_grid.data - floor_grid.data

            path = nav_grid.a_star(stuple, etuple, passable=DataGrid.zero_passable)

        if path is None:
            return [start, end]

        # Convert back to a path in three dimensions
        path3d = []
        for p in path:
            path3d.append(Vector3f(p[0], start.y, p[1]))

        return path3d

    async def on_headset_updated(self, event, uri, *args, **kwargs):
        current = kwargs.get('current')
        previous = kwargs.get('previous')

        # server/headset/models: describes the Headset class that the code is receiving

        if current.location_id is None:
            return

        if current.position is None or previous.position is None:
            return

        # If the time difference is too long, we cannot safely infer that
        # the line between the two points is passable
        if current.updated - previous.updated > MAXIMUM_TIME_DIFFERENCE:
            return

        if current.location_id not in self.floors:
            self.floors[current.location_id] = DataGrid(width=10.0, height=10.0, left=-5.0, top=-5.0)

        floor_grid = self.floors[current.location_id]

        # TODO: Change to have multiple floors in a single location and differentiate between each using y position

        floor_grid.add_segment(previous.position.totuple(), current.position.totuple(), vspread=1)

        now = time.time()
        if now - self.last_saved > SAVE_INTERVAL:
            floor_grid.save_image("floor-{}.png".format(current.location_id))
            self.last_saved = now

        # TODO: Change to put line in floor
        #floor.put_line([(previous.position.x, previous.position.z),
        #                (current.position.x, current.position.z)])
        #floor.user_locations.write_png("heatmap-{}.png".format(current.location_id))

        #print("Headset in location {} moved from {} to {}".format(
        #    current.location_id, previous.position, current.position))

        # current.position.x, current.position.z

        # TODO: use the old and new position to mark passable cells in the map
