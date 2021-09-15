# edge-server

This module coordinates interactions between multiple AR headsets, collects map and position changes from them, and disseminates important updates to all of the headsets. The primary functionality is exposed through an HTTP-based API and web interface, as shown below. Other edge compute tasks like computer vision will probably go in a separate module. This module could use a more clever name.

AR headset <- HTTP -> edge-server <- HTTP -> App or web interface

# API

The API specification is divided into functions intended for the headsets and for the app/web user interface, although there will be some overlap.

## AR Headset API

* Authenticate / register device
* Update map data: TBD whether these are individual points, surfaces, point clouds, and whether we have color or other image data
* Update position: TBD how to handle the coordinate systems of different headsets
* Get map features: return features to be rendered in AR, possibly filter by location or proximity
* Send an image or DNN intermediate layer for classification (included for completeness, but this probably should go through a different protocol)

## Web Interface API

* Authenticate user
* Get combined map data
* Get position of wearable device(s)
* Add a map feature: this could be a waypoint for directions, a target, a point of interest and may include rendering information such as text, arrows, polygons, colors, display duration, position hint (e.g. top of screen), or an image
