from quart import Quart

from server.headset.headsetroutes import blueprint
from server.maps import maps

app = Quart(__name__)
app.register_blueprint(blueprint)
app.register_blueprint(maps)
