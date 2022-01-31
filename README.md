# edge-server

This module coordinates interactions between multiple AR headsets, collects map and position changes from them, and disseminates important updates to all of the headsets. The primary functionality is exposed through an HTTP-based API and web interface, as shown below. Other edge compute tasks like computer vision will probably go in a separate module. This module could use a more clever name.

AR headset <- HTTP -> edge-server <- HTTP -> App or web interface

# Setup

Install dependencies.

```console
python3 -m pip install -r requirements.txt
```

Run the server with default settings. By default, it will listen on localhost port 5000 and look in the running directory for data and configuration files.

```console
python3 -m server
```

Run all of the unit tests.

```console
python3 -m pytest
```

Alternatively, build and run using Docker.

```console
docker build -t vizar-edge-server .
docker run --rm -p 5000:5000/tcp --name vizar-edge-server vizar-edge-server
```

# API

One function for the edge server is to provide a central exchange point for collaboration between multiple headset users. Therefore, the edge API will be consumed by a variety of applications including code running on the AR headset, a web interface, and even an Android app.

The latest version of the API specification can be found [here](https://easyvizar.github.io/edge-server/apispec.html). This document is automatically produced from comments in the code by using the apispec library.

To the extent it is reasonable, we plan to adhere to the [REST API design principles](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design).

## Example JSON Objects

### Headset Object

```json
{
    "id": "337329fb-4c07-4957-8bbe-072a92817ea3",
    "name": "Headset 3",
    "position": {
        "x": 10,
        "y": 10,
        "z": 10
    },
    "mapID": "b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6",
    "lastUpdate": "2021-09-21 14:06:39",
}
```

### Map Object

```json
{
    "id": "b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6",
    "name": "CS 7th Floor",
    "image": "/images/maps/b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6.png"
}
```

### Map Feature Object

```json
{
    "id": "c4b1e5bb-9e2a-4f76-987b-9ece3e06639e",
    "name": "Office",
    "position": {
        "x": 0,
        "y": 0,
        "z": 0
    },
    "mapID": "b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6",
    "style": {
        "placement": "floating|surface|point",
        "topOffset": "10%",
        "leftOffset": "10%",
        "icon": "/images/icons/marker.png"
    }
}
```

### Headset Update Object

```json
{
    "headsetID": "337329fb-4c07-4957-8bbe-072a92817ea3",
    "position": {
        "x": 20,
        "y": 20,
        "z": 20
    },
    "mapID": "b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6"
}
```

### Image Upload Object

```json
{
    "id": "5586018a-761c-4a93-a3fa-bb7f4e354626",
    "url": "/images/uploads/5586018a-761c-4a93-a3fa-bb7f4e354626.png",
    "intent": "maps|features|detection",
    "data": { "mapID": "b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6" },
    "type": "image/png"
}
```

When calling POST /image-uploads, the client provides the intent, data, and type fields.
The data field depends on the intent and will be passed to that module. For a map image,
it should include the map ID. For a feature, it should include bounding box(es) and
feature labels. Type is a MIME type such as "image/png" or "image/jpeg".

When responding to POST /image-uploads, the server fills in the id and url fields based
on the information in the request. The url field tells the client where to upload the
image file itself.

## Position of Features in AR

Here a few ways the API can specify the position of map features (points, symbols, or polygons) to be displayed in AR.

* Floating placement – a number of pixels or percentage from the top, bottom, left, or right of the screen
* Surface placement – on a floor or wall surface, centered or placed at an offset from the edge of the surface
* Point placement – a marker placed at a specified coordinate in space either relative to the headset or in a global coordinate system
