import os

from quart import Quart, g
from quart_cors import cors

from server.annotation.routes import annotations
from server.feature.routes import features
from server.headset.routes import headsets
from server.incidents.routes import initialize_incidents, incidents
from server.layer.routes import layers
from server.location.routes import locations
from server.maps.maps_routes import initialize_maps, maps
from server.photo.routes import photos
from server.pose_changes.routes import pose_changes
from server.routes import routes
from server.surface.routes import surfaces
from server.utils.utils import GenericJsonEncoder
from server.work_items.routes import work_items

from server.headset.models import Headset
from server.incidents.models import Incident

from server.resources.abstractresource import AbstractCollection

static_folder = os.environ.get("VIZAR_STATIC_FOLDER", "./frontend/build/")

app = Quart(__name__, static_folder=static_folder, static_url_path='/')
app = cors(app)

app.json_encoder = GenericJsonEncoder

# Use less-strict matching for trailing slashes in URLs. This is more likely to
# match user intent. For example, the following two requests are treated the same
# with strict_slashes disabled.
#
# GET /headsets
# GET /headsets/
app.url_map.strict_slashes = False

app.config.from_pyfile('default_settings.py')
if 'APPLICATION_CONFIG' in os.environ:
    app.config.from_envvar('APPLICATION_CONFIG')

# Configure the resource collections to use the appropriate top-level data
# directory. Configuring them once at application initialization avoids
# complicated dependencies on the app object.
data_dir = app.config.get('VIZAR_DATA_DIR', 'data')
AbstractCollection.data_directory = data_dir

app.register_blueprint(annotations)
app.register_blueprint(features)
app.register_blueprint(headsets)
app.register_blueprint(incidents)
app.register_blueprint(layers)
app.register_blueprint(locations)
app.register_blueprint(maps)
app.register_blueprint(photos)
app.register_blueprint(pose_changes)
app.register_blueprint(routes)
app.register_blueprint(surfaces)
app.register_blueprint(work_items)

@app.before_first_request
def before_first_request():
    # Make sure an active incident exists before initialize_maps is called.
    # This can be removed after we migrate to locations and layers.
    initialize_incidents(app)

    # Initialize maps storage and create the first map if there is not one.
    initialize_maps(app)

@app.before_request
def before_request():
    g.Headset = Headset
    g.Incident = Incident

    # Make sure an active incident exists and is assigned to g.active_incident.
    initialize_incidents(app)
