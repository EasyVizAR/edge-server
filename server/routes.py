from quart import Blueprint, render_template, url_for

routes = Blueprint('routes', __name__)

@routes.route("/")
@routes.route("/index")
@routes.route("/home")
async def home():
    return await render_template('home.html', title='Home')

@routes.route("/new_map")
async def new_map():
    return await render_template('new_map.html', title='New Map')
