import os

from quart import Quart
from quart_cors import cors

from server.headset.headsetroutes import blueprint as headset_blueprint
from server.maps.maps_routes import initialize_maps, maps
from server.incidents.incidents_routes import incidents
from server.work_items.routes import work_items
from server.routes import routes
from server.utils.utils import GenericJsonEncoder

app = Quart(__name__, static_folder='./frontend/build/', static_url_path='/')
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

app.register_blueprint(headset_blueprint)
app.register_blueprint(maps)
app.register_blueprint(work_items)
app.register_blueprint(routes)
app.register_blueprint(incidents)

@app.before_first_request
def before_first_request():
    # Initialize maps storage and create the first map if there is not one.
    initialize_maps(app)
