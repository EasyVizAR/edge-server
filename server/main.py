import os

from quart import Quart

from server.headset.headsetroutes import blueprint as headset_blueprint
from server.maps.maps_routes import maps
from server.meshes.routes import meshes
from server.routes import routes

app = Quart(__name__)

app.config.from_pyfile('default_settings.py')
if 'APPLICATION_CONFIG' in os.environ:
    app.config.from_envvar('APPLICATION_CONFIG')

app.register_blueprint(headset_blueprint)
app.register_blueprint(maps)
app.register_blueprint(meshes)
app.register_blueprint(routes)

