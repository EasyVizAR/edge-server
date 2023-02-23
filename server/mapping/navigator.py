"""
This stub class is an example of how we can integrate navigation functionality
in the server. The server will create one instance of this class at startup,
and connect the on_headset_updated method to the event dispatcher so that it
fires whenever a headset is updated. This gives an opportunity to observe user
movements in real-time to update the map with passability information. Since
there is only one navigator instance for the server, we will need to use the
passed location_id to look up the appropriate map.
"""

from .grid import Grid


class Navigator:
    def __init__(self):
        self.exploration_grids = dict()

    def find_path(self, location, start, end):
        layers = location.Layer.find(type="generated")

        # If there is no map, we cannot navigate!
        if len(layers) == 0:
            return [start, end]

        # This is the floor plan layer assuming we have only one floor
        layer = layers[0]

        # This would be the file path for the SVG image
        # layer.imagePath

        # TODO: run path finding algorithm here
        return [start, end]

    async def on_headset_updated(event, uri, *args, **kwargs):
        current = kwargs.get('current')
        previous = kwargs.get('previous')

        if current.location_id is None:
            return

        if current.position is None or previous.position is None:
            return

        if current.location_id not in self.exploration_grids:
            self.exploration_grids[current.location_id] = Grid(5)

        # Experimental code that should make a heatmap of explored areas
        # using the Grid class.
        grid = self.exploration_grids[current.location_id]
        grid.put_line([(previous.position.x, previous.position.z),
                        (current.position.x, current.position.z)])
        grid.write_png("heatmap.png")

        #print("Headset in location {} moved from {} to {}".format(
        #    current.location_id, previous.position, current.position))

        # TODO: use the old and new position to mark passable cells in the map
