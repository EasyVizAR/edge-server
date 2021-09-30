from quart import Quart

from server.headset.headsetroutes import blueprint

app = Quart(__name__)
app.register_blueprint(blueprint)