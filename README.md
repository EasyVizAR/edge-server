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

## API Function Specifications

The goal should be to follow REST API design practices to the extent that is reasonable.
See: https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design

| List headsets ||
| ---               | --- |
| URL               | /headsets |
| Method            | GET |
| URL Parameters    | N/A |
| Success Response  | Code: 200 OK <br \> Content: `[{ *headset* }, ...]` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }`|

| Show headset ||
| ---               | --- |
| URL               | /headsets/:id |
| Method            | GET |
| URL Parameters    | Required: <br \> `id=[GUID]` |
| Success Response  | Code: 200 OK <br \> Content: `{ *headset* }` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }` |
| Error Response    | Code: 404 NOT FOUND <br \> Content: `{ "error": "The requested headset does not exist." }` |

| List maps ||
| ---               | --- |
| URL               | /maps |
| Method            | GET |
| URL Parameters    | N/A |
| Success Response  | Code: 200 OK <br \> Content: `[{ *map* }, ...]` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }`|

| Show map ||
| ---               | --- |
| URL               | /maps/:id |
| Method            | GET |
| URL Parameters    | Required: <br \> `id=[GUID]` |
| Success Response  | Code: 200 OK <br \> Content: `{ *map* }` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }` |
| Error Response    | Code: 404 NOT FOUND <br \> Content: `{ "error": "The requested map does not exist." }` |

| List map features ||
| ---               | --- |
| URL               | /maps/:map-id/features |
| Method            | GET |
| URL Parameters    | Required: <br \> `map-id=[GUID]` |
| Success Response  | Code: 200 OK <br \> Content: `[{ *feature* }, ...]` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }`|
| Error Response    | Code: 404 NOT FOUND <br \> Content: `{ "error": "The requested map does not exist." }` |

| Add map feature ||
| ---               | --- |
| URL               | /maps/:map-id/features |
| Method            | POST |
| URL Parameters    | Required: <br \> `map-id=[GUID]` |
| Data              | `{ *map feature* }`
| Success Response  | Code: 201 CREATED <br \> Content: `{ *feature* }` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }`|
| Error Response    | Code: 404 NOT FOUND <br \> Content: `{ "error": "The requested map does not exist." }` |

| Update a headset position ||
| ---               | --- |
| URL               | /headsets/:headset-id/updates |
| Method            | POST |
| URL Parameters    | Required: <br \> `headset-id=[GUID]` |
| Data              | `{ *headset update* }`
| Success Response  | Code: 201 CREATED <br \> Content: `{ *headset update* }` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }`|
| Error Response    | Code: 404 NOT FOUND <br \> Content: `{ "error": "The requested headset does not exist." }` |

| Prepare an image upload ||
| ---               | --- |
| URL               | /image-uploads |
| Method            | POST |
| Data              | `{ *image upload* }`
| Success Response  | Code: 201 CREATED <br \> Content: `{ *image upload* }` |
| Error Response    | Code: 401 UNAUTHORIZED <br \> Content: `{ "error": "Not authorized. Please log in." }`|

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
