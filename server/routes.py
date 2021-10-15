from quart import Blueprint, render_template, url_for

routes = Blueprint('routes', __name__)

@routes.route("/")
@routes.route("/index")
@routes.route("/home")
def home():
    return render_template('home.html', title='Home')

@routes.route("/new_map")
def new_map():

    return render_template('new_map.html', title='New Map')
