from quart import Quart

from server.headset.headsetroutes import blueprint as headset_blueprint
from server.maps.maps_routes import maps
from server.routes import routes

app = Quart(__name__)
app.register_blueprint(headset_blueprint)
app.register_blueprint(maps)
app.register_blueprint(routes)
app.config.from_envvar('APPLICATION_CONFIG')
