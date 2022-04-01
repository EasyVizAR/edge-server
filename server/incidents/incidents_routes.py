from http import HTTPStatus
from quart import Blueprint, make_response, jsonify, current_app, request

from server.incidents.incident_handler import init_incidents_handler
from server.maps.maprepository import Repository, get_map_repository

incidents = Blueprint('incidents', __name__)


@incidents.route('/incidents/create/', methods=['POST'])
async def create_incident():
    body = await request.get_json()

    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    if 'incident_name' in body:
        incident_name = body.get('incident_name')
    else:
        incident_name = None

    incident_handler.create_new_incident(incident_name=incident_name)
    get_map_repository().reset_maps_for_new_incident()

    return await make_response(
        jsonify({"message": "Incident Created"}), HTTPStatus.CREATED)


@incidents.route('/incidents', methods=['GET'])
async def get_incident():
    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    curr_incident = incident_handler.current_incident
    curr_incident_name = incident_handler.get_incident_name(curr_incident)

    return await make_response(
        jsonify({"incident_number": str(curr_incident),
                 "incident_name": str(curr_incident_name)}),
        HTTPStatus.OK)


@incidents.route('/incidents/history', methods=['GET'])
async def get_past_incident_info():
    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    past_incidents = incident_handler.get_all_incident_info()

    return jsonify(past_incidents), HTTPStatus.OK


@incidents.route('/incidents/<incident_number>', methods=['DELETE'])
async def delete_incident(incident_number):
    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)
    deleted = incident_handler.delete_incident(incident_number)

    if deleted:
        return jsonify({'message': 'Incident Deleted'}), HTTPStatus.OK

    return jsonify({'message': 'Incident could not be deleted'}), HTTPStatus.BAD_REQUEST


@incidents.route('/incidents/<incident_number>', methods=['POST'])
async def update_incident_name(incident_number):
    # init incidents handler if it is not already
    incident_handler = init_incidents_handler(app=current_app)

    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'name' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    incident_handler.update_inident_name(str(incident_number), body['name'])

    return await make_response(
        jsonify({"message": "Name Updated"}),
        HTTPStatus.OK)
