from http import HTTPStatus
from quart import Blueprint, make_response, jsonify, current_app, request

from server.incidents.incident_handler import init_incidents_handler

incidents = Blueprint('incidents', __name__)


@incidents.route('/incidents/create/', methods=['POST'])
async def create_incident():

    body = await request.get_json()

    print(body)

    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    if 'incident_name' in body:
        incident_name = body.get('incident_name')
    else:
        incident_name = None

    incident_handler.create_new_incident(incident_name=incident_name)

    return await make_response(
        jsonify({"message": "Incident Created"}), HTTPStatus.CREATED)


@incidents.route('/incidents', methods=['GET'])
async def get_incident():

    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    curr_incident = incident_handler.current_incident
    curr_incident_name = incident_handler.curr_incident_name

    return await make_response(
        jsonify({"incident_number": str(curr_incident),
                 "incident_name": str(curr_incident_name)}),
        HTTPStatus.OK)
