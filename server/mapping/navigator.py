"""
This stub class is an example of how we can integrate navigation functionality
in the server. The server will create one instance of this class at startup,
and connect the on_headset_updated method to the event dispatcher so that it
fires whenever a headset is updated. This gives an opportunity to observe user
movements in real-time to update the map with passability information. Since
there is only one navigator instance for the server, we will need to use the
passed location_id to look up the appropriate map.
"""
from server.location.models import LocationModel
from server.resources.geometry import Vector3f
from .floor import Floor

class Navigator:
    def __init__(self):
        self.explored_buildings = {}

    def find_path(self, location: LocationModel, start, end):
        layers = location.Layer.find(type="generated")
        # from server/location/models

        # If there is no map, we cannot navigate!
        if len(layers) == 0:
            return [start, end]

        # This is the floor plan layer assuming we have only one floor
        layer = layers[0]

        # This would be the file path for the SVG image
        # layer.imagePath

        # headset.location_id and location.id are the same, use this information for identifying specific bluiding

        if location.id not in self.explored_buildings:
            self.explored_buildings[location.id] = Floor(5)
        
        floor = self.explored_buildings[location.id]

        floor.update_walls_from_svg(layer.imagePath)

        # Convert start and end from type Vector3f to type tuple
        path = floor.calculate_path((start.x, start.z), (end.x, end.z))

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

        if current.location_id not in self.explored_buildings:
            self.explored_buildings[current.location_id] = Floor(5)

        # TODO: Change to have multiple floors in a single location and differentiate between each using y position

        # Experimental code that should make a heatmap of explored areas
        # using the Grid class.
        floor = self.explored_buildings[current.location_id]

        # TODO: Change to put line in floor
        #floor.put_line([(previous.position.x, previous.position.z),
        #                (current.position.x, current.position.z)])
        #floor.user_locations.write_png("heatmap-{}.png".format(current.location_id))

        #print("Headset in location {} moved from {} to {}".format(
        #    current.location_id, previous.position, current.position))

        # current.position.x, current.position.z

        # TODO: use the old and new position to mark passable cells in the map
