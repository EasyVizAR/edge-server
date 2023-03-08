import os

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from quart import Quart, g

from server.annotation.routes import annotations
from server.check_in.routes import check_ins
from server.feature.routes import features
from server.headset.routes import headsets
from server.incidents.routes import initialize_incidents, incidents
from server.layer.routes import layers
from server.location.routes import locations
from server.photo.routes import photos
from server.pose_changes.routes import pose_changes
from server.routes import routes
from server.scene.routes import scenes
from server.surface.routes import surfaces
from server.utils.pool_limiter import PoolLimiter
from server.utils.rate_limiter import main_rate_limiter
from server.utils.utils import GenericJsonEncoder
from server.work_items.routes import work_items

from server.auth import Authenticator
from server.events import EventDispatcher
from server.headset.models import Headset
from server.incidents.models import Incident
from server.mapping.navigator import Navigator

from server.resources.abstractresource import AbstractCollection

static_folder = os.environ.get("VIZAR_STATIC_FOLDER", "./frontend/build/")

app = Quart(__name__, static_folder=static_folder, static_url_path='/')

main_rate_limiter.init_app(app)

# CORS seems to be breaking websocket connections but only when they set a
# specific header value.
#
# Connection: Upgrade -> broken
# Connection: keep-alive, Upgrade -> seems fine
#
# Unfortunately, we may not be able to change the websocket client
# implementation.
#app = cors(app)

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

blueprints = [
    annotations,
    check_ins,
    features,
    headsets,
    incidents,
    layers,
    locations,
    photos,
    pose_changes,
    routes,
    scenes,
    surfaces,
    work_items
]

for bp in blueprints:
    app.register_blueprint(bp)


@app.before_first_request
def before_first_request():
    app.authenticator = Authenticator.build_authenticator(data_dir)

    app.dispatcher = EventDispatcher()

    # Use a separate process pool for mapping and 3D modeling tasks so they can
    # run in parallel.
    app.mapping_pool = ProcessPoolExecutor(1)
    app.mapping_limiter = PoolLimiter()

    app.modeling_pool = ProcessPoolExecutor(1)
    app.modeling_limiter = PoolLimiter()

    # Thread pool for miscellaneous tasks like cleaning up old images.
    app.thread_pool = ThreadPoolExecutor()
    app.last_photo_cleanup = 0

    app.navigator = Navigator()
    app.dispatcher.add_event_listener("headsets:updated", "*", app.navigator.on_headset_updated)


@app.before_request
def before_request():
    # This will be set by the authenticator if the user
    # passed a valid credential.
    g.user_id = None

    g.authenticator = app.authenticator
    g.authenticator.authenticate_request()

    g.Headset = Headset
    g.Incident = Incident

    # Make sure an active incident exists and is assigned to g.active_incident.
    initialize_incidents(app)


@app.before_websocket
def before_websocket():
    # This will be set by the authenticator if the user
    # passed a valid credential.
    g.user_id = None

    g.authenticator = app.authenticator
    g.authenticator.authenticate_websocket()

    g.Headset = Headset
    g.Incident = Incident

    # Make sure an active incident exists and is assigned to g.active_incident.
    initialize_incidents(app)
