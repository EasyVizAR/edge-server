# EasyVizAR Edge Server

The EasyVizAR edge server coordinates interactions between AR devices, collects
map, position, and image data from mobile devices, and disseminates important
updates to all of the connected devices. The primary functionality is exposed
through an HTTP-based API following REST principles and through a web-based
dashboard. Other compute tasks such as object detection in images are
accomplished through add-on modules that can be installed separately.

AR headset <- HTTP -> edge-server <- HTTP -> App or web interface

# Recommended Installation

The recommended installation assumes an Ubuntu LTS server and relies on snaps
for distribution and automatic updates. Snaps contain most of the application
dependencies, so these instructions should work on various Ubuntu versions
including 18.04 through 22.04.

Install the EasyVizAR edge server. By default, this will pull from the stable
branch, which will only receive infrequent and tested releases.

```console
sudo snap install easyvizar-edge
```

If you experience database migration errors (e.g. "table pose_changes already
exists") that block the snap from refreshing, especially on the stable or
candidate channels, you may have a version of the snap that does not currectly
track the database schema version. The following command should fix the
database version, after which you can retry the `snap refresh` command.

```console
sudo snap run --shell easyvizar-edge.server -c 'cd $SNAP_DATA; cp $SNAP/alembic.ini .; ln -sf "$SNAP/alembic" .; alembic stamp head'
```

The server will listen on port 5000 and can be tested by directing a web
browser to the server address and port, e.g. `http://example.org:5000`.
However, in a production setting, it is recommended to block external traffic
to port 5000 and instead use a proxy, such as nginx as described below.

Install nginx and the rtmp module.

```console
sudo apt-get update && sudo apt-get install nginx libnginx-mod-rtmp
```

(Optional but recommended) Install the Let's Encrypt certbot for free SSL
certificates, in order to enable HTTPS connections.

```console
sudo snap install certbot --classic
```

Request a certificate for the server's domain name.

```console
sudo certbot run --nginx -d EXAMPLE.ORG
```

Then customize the nginx configuration and restart the nginx server. A couple
of recommended options are enabling the rtmp module for real-time video
streaming and enabling automatic redirects from HTTP to HTTPS. Example
configuration files are provided in the `environment` folder.

```console
sudo systemctl restart nginx
```

The server should now be available and can be tested by directing a web
browser to the intended domain name, e.g. `https://example.org`.

(Optional) Install the easyvizar-detect add-on module. This module
automatically performs object detection on any photos uploaded to the edge
server. It is currently experimental and may cause performance issues.

```console
sudo snap install easyvizar-detect
```

# Post-Installation Setup

## Users and Authentication

When the server starts for the first time, it will create three default user
accounts: admin, user, and guest. The admin and user accounts will be
configured with randomly generated passwords that can be found in the log
output.  The guest account will have no password configured by default.  If
installed as a snap, the following command will reveal the default account
passwords. You may need to open a connection to the server through a web
browser one time in order for the initialization to complete.

```console
sudo snap logs -n=all easyvizar-edge | grep user
```

It is recommended to change the admin and user account passwords after
installation. This can be done on the Users page of the web dashboard if
logged in as an admin user. The default admin and user accounts should not
be deleted.  However, the guest account can be safely deleted if desired.

## Create a Location

In the EasyVizAR system, a *location* is any defined physical space to
which virtual content can be anchored. A location might be a multi-floor
office building, for example. The server will generate a unique QR code
for each location. By scanning the QR code, EasyVizAR-capable devices can
report their presence and synchronize their virtual coordinate system,
with the QR code serving as the origin of the coordinate system.

Navigate to the Locations page on the web dashboard and use the form to
create a new location. Then click on the newly-created location ID link in
the table to go to page for that location. Initially, the map and tables
will be empty but will be populated as devices join the location and send
data. Click on the *Location QR Code* button to generate a QR code. It
is recommended to print the QR code on letter size paper and afix it
**horizontally** to a flat surface in the environment, roughly between
waist and eye-level. Taping it to a table works well.  The coordinate
system for the location will have its origin at the center of the QR
code, X-axis pointing to the right edge of the page, Y-axis pointing up
from the QR code, and Z-axis pointing toward the top edge of the page.
Floor plan maps will be generated in the same orientation as the QR code
(imagine the QR code block were replaced with a map), so you may wish to
orient the page according to how you would like the map to be generated.

# Installation from Source

Install dependencies.

```console
python3 -m pip install -r requirements.txt
```

Run the server with default settings. By default, it will listen on localhost
port 5000 and look in the running directory for data and configuration files.

```console
python3 -m server
```

Run the server in development mode. This enables certain useful functions such
as additional websocket commands which would be dangerous in deployment.

```console
QUART_ENV=development python3 -m server
```

Run all of the unit tests with coverage report.

```console
QUART_ENV=testing python3 -m pytest --ignore scripts --cov=server --cov-report term-missing:skip-covered
```

Alternatively, build and run using Docker.

```console
docker build -t easyvizar-edge-server .
docker run --rm -p 5000:5000/tcp --name easyvizar-edge-server easyvizar-edge-server
```

# Design

![Class UML Diagram](./docs/classes.svg)

# API

One function for the edge server is to provide a central exchange point for
collaboration between multiple headset users. Therefore, the edge API will be
consumed by a variety of applications including code running on the AR headset,
a web interface, and even an Android app.

The latest version of the API specification can be found on any running edge
server by navigating to the `/openapi.html` page or by clicking through the user
menu in the top right corner of the dashboard. This document is automatically
produced from comments in the code by using the apispec library.

To the extent it is reasonable, we adhere to the [REST API design principles](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design).
