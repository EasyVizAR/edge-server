from http import HTTPStatus

from quart import Blueprint, g, make_response, jsonify, current_app, redirect, request
from werkzeug import exceptions

from server.incidents.models import Incident

incidents = Blueprint('incidents', __name__)


def initialize_incidents(app):
    """
    Initialize incidents module at application startup.

    This ensures that at least one incident exists, and we determine the ID of
    the current active incident.
    """
    incident = None

    # First check if an active incident is configured globally.
    incident_id = app.config.get('ACTIVE_INCIDENT_ID')
    if incident_id is not None:
        incident = Incident.find_by_id(incident_id)

    # Active incident may not be configured, or it may have been deleted.
    if incident is None:
        incident = Incident.find_newest()

    # If still no incident is found, create one.
    if incident is None:
        incident = Incident(name="Incident 1")
        incident.save()

    set_active_incident(app, incident)


def set_active_incident(app, incident):
    app.config['ACTIVE_INCIDENT_ID'] = incident.id
    g.active_incident = incident


@incidents.route('/incidents', methods=['GET'])
async def list_incidents():
    """
    List incidents
    ---
    get:
        summary: List incidents
        tags:
         - incidents
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Incident
    """
    incidents = g.Incident.find()

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): incidents}
    else:
        result = incidents

    return jsonify(result), HTTPStatus.OK


@incidents.route('/incidents', methods=['POST'])
async def create_incident():
    """
    Create incident
    ---
    post:
        summary: Create incident
        description: A side effect of this method is that the newly created
            incident will become the current active incident.
        tags:
         - incidents
        requestBody:
            required: true
            content:
                application/json:
                    schema: Incident
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: Incident
    """
    body = await request.get_json()

    incident = g.Incident.load(body, replace_id=True)
    incident.save()

    set_active_incident(current_app, incident)

    return jsonify(incident), HTTPStatus.CREATED


@incidents.route('/incidents/<incident_id>', methods=['DELETE'])
async def delete_incident(incident_id):
    """
    Delete incident
    ---
    delete:
        summary: Delete incident
        tags:
         - incidents
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be deleted
        responses:
            200:
                description: The object which was deleted
                content:
                    application/json:
                        schema: Incident
    """
    incident = g.Incident.find_by_id(incident_id)
    if incident is None:
        raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

    incident.delete()

    return jsonify(incident), HTTPStatus.OK


@incidents.route('/incidents/<incident_id>', methods=['GET'])
async def get_incident(incident_id):
    """
    Get incident
    ---
    get:
        summary: Get incident
        tags:
         - incidents
        parameters:
          - name: id
            in: path
            required: true
            description: Object ID
        responses:
            200:
                description: The requested object
                content:
                    application/json:
                        schema: Incident
    """
    incident = g.Incident.find_by_id(incident_id)
    if incident is None:
        raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

    return jsonify(incident), HTTPStatus.OK


@incidents.route('/incidents/<incident_id>', methods=['PUT'])
async def replace_incident(incident_id):
    """
    Replace incident
    ---
    put:
        summary: Replace incident
        description: A side effect of this method is that the newly created
            incident will become the current active incident.
        tags:
         - incidents
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Incident
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Incident
    """
    body = await request.get_json()
    body['id'] = incident_id

    incident = g.Incident.load(body)
    created = incident.save()

    set_active_incident(current_app, incident)

    if created:
        return jsonify(incident), HTTPStatus.CREATED
    else:
        return jsonify(incident), HTTPStatus.OK


@incidents.route('/incidents/<incident_id>', methods=['PATCH'])
async def update_incident(incident_id):
    """
    Update incident
    ---
    patch:
        summary: Update incident
        description: This method may be used to modify selected fields of the object.
            Updating an incident will not cause it to become the active incident.
        tags:
         - incidents
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Incident
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Incident
    """

    incident = g.Incident.find_by_id(incident_id)
    if incident is None:
        raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    incident.update(body)
    incident.save()

    return jsonify(incident), HTTPStatus.OK


@incidents.route('/incidents/active', methods=['GET'])
async def get_active_incident():
    """
    Get the current active incident
    ---
    get:
        summary: Get the current active incident
        tags:
          - incidents
        responses:
            200:
                description: An Incident object
                content:
                    application/json:
                        schema: Incident
    """
    if g.active_incident is None:
        return jsonify({'message': 'Active incident not found'}), HTTPStatus.NOT_FOUND

    else:
        return jsonify(g.active_incident), HTTPStatus.OK


@incidents.route('/incidents/active', methods=['PUT'])
async def change_active_incident():
    """
    Change the current active incident
    ---
    put:
        summary: Change the current active incident
        tags:
          - incidents
        responses:
            200:
                description: An Incident object
                content:
                    application/json:
                        schema: Incident
    """
    body = await request.get_json()

    if not body:
        return await make_response(
            jsonify({"message": "Missing body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    if 'id' not in body:
        return await make_response(
            jsonify({"message": "Missing parameter in body",
                     "severity": "Warning"}),
            HTTPStatus.BAD_REQUEST)

    incident = g.Incident.load(body)

    set_active_incident(current_app, incident)

    return jsonify(incident), HTTPStatus.OK


#
# The following functions are either deprecated or untested.
#


@incidents.route('/incidents/history', methods=['GET'])
async def get_past_incident_info():
    """
    (deprecated) caller should use GET /incidents to get list of incidents
    """
    return redirect("/incidents")
