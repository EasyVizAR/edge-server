"""
This stub class is an example of how we can integrate navigation functionality
in the server. The server will create one instance of this class at startup,
and connect the on_headset_updated method to the event dispatcher so that it
fires whenever a headset is updated. This gives an opportunity to observe user
movements in real-time to update the map with passability information. Since
there is only one navigator instance for the server, we will need to use the
passed location_id to look up the appropriate map.
"""

from floor import Floor

class Navigator:

    def find_path(self, location, start, end):
        layers = location.Layer.find(type="generated")

        # If there is no map, we cannot navigate!
        if len(layers) == 0:
            return [start, end]

        # This is the floor plan layer assuming we have only one floor
        layer = layers[0]

        # This would be the file path for the SVG image
        # layer.imagePath

        # What would the layer.imagePath even look like? Would it be relative to the edge-server repository?

        floor = Floor()
        floor.update_walls_from_svg()

        # TODO: run path finding algorithm here
        return [start, end]

    async def on_headset_updated(self, event, uri, *args, **kwargs):
        current = kwargs.get('current')
        previous = kwargs.get('previous')

        # server/headset/models: describes the Headset class that the code is receiving

        if current.location_id is None:
            return

        if current.position is None or previous.position is None:
            return

        #print("Headset in location {} moved from {} to {}".format(
        #    current.location_id, previous.position, current.position))

        # current.position.x, current.position.z

        # TODO: use the old and new position to mark passable cells in the map
