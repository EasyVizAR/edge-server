import datetime
import uuid

from http import HTTPStatus

from quart import Blueprint, g, make_response, jsonify, current_app, redirect, request
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server import auth
from server.utils.response import maybe_wrap

from .models import Incident, IncidentSchema


incidents = Blueprint('incidents', __name__)

incident_schema = IncidentSchema()


async def initialize_incidents(app):
    """
    Initialize incidents module at application startup.

    This ensures that at least one incident exists, and we determine the ID of
    the current active incident.
    """
    g.active_incident = await find_active_incident(app)
    g.active_incident_id = g.active_incident.id
    app.config['ACTIVE_INCIDENT_ID'] = g.active_incident.id


async def find_active_incident(app):
    incident_id = app.config.get('ACTIVE_INCIDENT_ID')
    if isinstance(incident_id, str):
        try:
            incident_id = uuid.UUID(app.config.get('ACTIVE_INCIDENT_ID'))
        except:
            incident_id = None

    async with g.session_maker() as session:
        if incident_id is not None:
            stmt = sa.select(Incident).where(Incident.id == incident_id).limit(1)
            result = await session.execute(stmt)
            incident = result.scalar()

            if incident is not None:
                return incident

        stmt = sa.select(Incident).order_by(Incident.updated_time.desc()).limit(1)
        result = await session.execute(stmt)
        incident = result.scalar()

        if incident is None:
            incident = Incident(id=uuid.uuid4())
            session.add(incident)
            await session.commit()

        return incident


def set_active_incident(app, incident):
    app.config['ACTIVE_INCIDENT_ID'] = incident.id
    g.active_incident = incident
    g.active_incident_id = incident.id


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
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(Incident)
        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(incident_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


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
    body['id'] = uuid.uuid4()

    incident = incident_schema.load(body, transient=True)

    async with g.session_maker() as session:
        session.add(incident)
        await session.commit()

    set_active_incident(current_app, incident)

    result = incident_schema.dump(incident)

    return jsonify(result), HTTPStatus.CREATED


@incidents.route('/incidents/<uuid:incident_id>', methods=['DELETE'])
@auth.requires_admin
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
    async with g.session_maker() as session:
        stmt = sa.select(Incident) \
                .where(Incident.id == incident_id) \
                .limit(1)

        result = await session.execute(stmt)
        incident = result.scalar()
        if incident is None:
            raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

        await session.delete(incident)
        await session.commit()

    result = incident_schema.dump(incident)

    return jsonify(result), HTTPStatus.OK


@incidents.route('/incidents/<uuid:incident_id>', methods=['GET'])
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
    async with g.session_maker() as session:
        stmt = sa.select(Incident) \
                .where(Incident.id == incident_id) \
                .limit(1)

        result = await session.execute(stmt)
        incident = result.scalar()
        if incident is None:
            raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

    result = incident_schema.dump(incident)

    return jsonify(result), HTTPStatus.OK


@incidents.route('/incidents/<uuid:incident_id>', methods=['PUT'])
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
    if body is None:
        body = {}
    body['id'] = incident_id

    async with g.session_maker() as session:
        stmt = sa.select(Incident) \
                .where(Incident.id == incident_id) \
                .limit(1)

        result =await session.execute(stmt)
        incident = result.scalar()

        if incident is None:
            incident = incident_schema.load(body, transient=True)
            session.add(incident)
            created = True

        else:
            incident.update(body)
            incident.updated_time = datetime.datetime.now()
            created = False

        await session.commit()

    result = incident_schema.dump(incident)

    set_active_incident(current_app, incident)

    if created:
        return jsonify(result), HTTPStatus.CREATED
    else:
        return jsonify(result), HTTPStatus.OK


@incidents.route('/incidents/<uuid:incident_id>', methods=['PATCH'])
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
    body = await request.get_json()

    async with g.session_maker() as session:
        stmt = sa.select(Incident) \
                .where(Incident.id == incident_id) \
                .limit(1)

        result = await session.execute(stmt)
        incident = result.scalar()
        if incident is None:
            raise exceptions.NotFound(description="Incident {} was not found".format(incident_id))

        incident.update(body)
        incident.updated_time = datetime.datetime.now()
        await session.commit()

    result = incident_schema.dump(incident)

    return jsonify(result), HTTPStatus.OK


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
        result = incident_schema.dump(g.active_incident)
        return jsonify(result), HTTPStatus.OK


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

    incident = incident_schema.load(body, transient=True)
    set_active_incident(current_app, incident)
    result = incident_schema.dump(incident)
    return jsonify(result), HTTPStatus.OK
