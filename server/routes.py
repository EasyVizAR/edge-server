import quart
from quart import Blueprint, render_template, url_for

routes = Blueprint('routes', __name__)


@routes.route('/')
async def index():
    return await quart.current_app.send_static_file('index.html')

@routes.route("/new_map")
async def new_map():
    return await render_template('new_map.html', title='New Map')
