from http import HTTPStatus
from quart import Blueprint, make_response, jsonify

from quart import current_app
from server.incidents.incident_handler import init_incidents_handler

incidents = Blueprint('incidents', __name__)


@incidents.route('/incidents/create', methods=['POST'])
async def create_incident():

    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)
    incident_handler.create_new_incident()

    return await make_response(
        jsonify({"message": "Incident Created"}), HTTPStatus.CREATED)


@incidents.route('/incidents', methods=['GET'])
async def get_incident():

    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)
    print('incident found: ' + str(incident_handler.current_incident))
    return await make_response(
        jsonify({"incident": str(incident_handler.current_incident)}),
        HTTPStatus.OK)
