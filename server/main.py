import os

from quart import Quart
from quart_cors import cors

from server.headset.headsetroutes import blueprint as headset_blueprint
from server.maps.maps_routes import initialize_maps, maps
from server.routes import routes

app = Quart(__name__, static_folder='./frontend/build/', static_url_path='/')
app = cors(app)

app.config.from_pyfile('default_settings.py')
if 'APPLICATION_CONFIG' in os.environ:
    pass
    #app.config.from_envvar('APPLICATION_CONFIG')

app.register_blueprint(headset_blueprint)
app.register_blueprint(maps)
app.register_blueprint(routes)

# Initialize maps storage and create the first map if there is not one.
initialize_maps(app)
