from quart import Quart

from server.headset.headsetroutes import blueprint as headset_blueprint

app = Quart(__name__)
app.register_blueprint(headset_blueprint)
app.config.from_envvar('APPLICATION_CONFIG')
