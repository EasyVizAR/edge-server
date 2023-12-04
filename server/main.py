import os
import tempfile

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import magic

from quart import Quart, g
from quart_sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.check_in.routes import check_ins
from server.feature.routes import features
from server.headset.routes import headsets
from server.incidents.routes import initialize_incidents, incidents
from server.layer.routes import layers
from server.location.routes import locations
from server.photo.routes import photos
from server.pose_changes.routes import pose_changes
from server.routes import routes
from server.streams import streams
from server.surface.routes import surfaces
from server.utils.pool_limiter import PoolLimiter
from server.utils.rate_limiter import main_rate_limiter
from server.utils.utils import GenericJsonEncoder
from server.websocket.routes import websockets

from server.auth import Authenticator, initialize_users_table
from server.events import EventDispatcher
from server.mapping.navigator import Navigator
from server.mapping2.mapper import Mapper
from server.models.base import Base


sqlite_file = "easyvizar-edge.sqlite"

static_folder = os.environ.get("VIZAR_STATIC_FOLDER", "./frontend/build/")

app = Quart(__name__, static_folder=static_folder, static_url_path='/')

engine = create_async_engine("sqlite+aiosqlite:///"+sqlite_file)
session_maker = async_sessionmaker(engine, expire_on_commit=False)


if os.path.exists(sqlite_file):
    print("Skipping database initialization because {} exists".format(sqlite_file))
else:
    print("Initializing sqlite database, stored at {}".format(sqlite_file))
    sync_engine = create_engine("sqlite:///"+sqlite_file)
    Base.metadata.create_all(sync_engine)


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

blueprints = [
    check_ins,
    features,
    headsets,
    incidents,
    layers,
    locations,
    photos,
    pose_changes,
    routes,
    streams,
    surfaces,
    websockets
]

for bp in blueprints:
    app.register_blueprint(bp)


@app.before_first_request
async def before_first_request():
    app.authenticator = Authenticator.build_authenticator(data_dir)

    app.session_maker = session_maker

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

    app.navigator = Navigator(data_dir=data_dir)
    app.dispatcher.add_event_listener("headsets:updated", "*", app.navigator.on_headset_updated)

    app.mapper = Mapper(data_dir=data_dir)
    app.dispatcher.add_event_listener("surfaces:updated", "*", app.mapper.on_surface_updated)

    # Create a temporary directory for transient files
    app.temp_dir = tempfile.mkdtemp()

    # The magic library makes it easy to identify file types of uploaded files.
    # Annoyingly, we need to track down the location of the magic database when
    # installed as a snap.
    if "SNAP" in os.environ:
        magic_file = os.path.join(os.environ['SNAP'], "usr/lib/file/magic.mgc")
        app.magic = magic.Magic(magic_file=magic_file, mime=True)
    else:
        app.magic = magic.Magic(mime=True)

    # Make sure some users are defined
    await initialize_users_table(app)


@app.before_request
async def before_request():
    g.data_dir = data_dir
    g.temp_dir = app.temp_dir

    g.environment = os.environ.get("QUART_ENV", "production")

    # This will be set by the authenticator if the user
    # passed a valid credential.
    g.device_id = None
    g.user_id = None
    g.user = None

    g.session_maker = session_maker
    g.session = session_maker()

    g.authenticator = app.authenticator
    await g.authenticator.authenticate_request()

    # Make sure an active incident exists and is assigned to g.active_incident.
    await initialize_incidents(app)


@app.after_request
async def after_request(response):
    await g.session.close()

    return response


@app.before_websocket
async def before_websocket():
    g.data_dir = data_dir
    g.temp_dir = app.temp_dir

    g.environment = os.environ.get("QUART_ENV", "production")

    # This will be set by the authenticator if the user
    # passed a valid credential.
    g.device_id = None
    g.user_id = None
    g.user = None

    g.session_maker = session_maker
    g.session = session_maker()

    g.authenticator = app.authenticator
    await g.authenticator.authenticate_websocket()

    # Make sure an active incident exists and is assigned to g.active_incident.
    await initialize_incidents(app)


@app.after_websocket
async def after_websocket(response):
    await g.session.close()

    return response
