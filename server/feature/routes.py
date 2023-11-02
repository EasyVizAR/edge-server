import datetime

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request
from werkzeug import exceptions

import marshmallow
import sqlalchemy as sa

from server.location.models import Location
from server.utils.response import maybe_wrap

from .models import MapMarker, FeatureSchema


features = Blueprint("features", __name__)

feature_schema = FeatureSchema()


# Color palette for features.  This is the Tol muted palette, which is
# distinguishable for colorblind vision.
default_color_palette = [
    "#cc6677",
    "#332288",
    "#ddcc77",
    "#117733",
    "#88ccee",
    "#44aa99",
    "#999933",
    "#aa4499"
]


@features.route('/locations/<uuid:location_id>/features', methods=['GET'])
async def list_features(location_id):
    """
    List features
    ---
    get:
        summary: List features
        tags:
         - features
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
                            items: Feature
    """
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(MapMarker).where(MapMarker.location_id == location_id)
        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(feature_schema.dump(row))

    await current_app.dispatcher.dispatch_event("features:viewed", "/locations/{}/features".format(str(location_id)))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@features.route('/locations/<uuid:location_id>/features', methods=['POST'])
async def create_feature(location_id):
    """
    Create feature
    ---
    post:
        summary: Create feature
        description: |-
            Create a new map feature, which can be one of many kinds of digital
            information attached to a physical space.

            The following example creates a marker at a specific point:

                POST /locations/<location_id>/features
                Content-Type: application/json
                {
                    "name": "Main Stairwell",
                    "type": "stairs",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "style": {"placement": "point"}
                }
        tags:
         - features
        requestBody:
            required: true
            content:
                application/json:
                    schema: Feature
        responses:
            200:
                description: The created object
                content:
                    application/json:
                        schema: Feature
    """
    body = await request.get_json()

    async with g.session_maker() as session:
        stmt = sa.select(Location).where(Location.id == location_id).limit(1)
        result = await session.execute(stmt)
        location = result.scalar()
        if location is None:
            raise execptions.NotFound(description="Location {} was not found".format(location_id))

        if g.user_id is not None:
            body['user_id'] = uuid.UUID(g.user_id)

        marker = feature_schema.load(body, transient=True)
        marker.location_id = location_id
        session.add(marker)
        await session.commit()

        # Choose a color for the feature by cycling through the palette.
        if body.get("color") in [None, ""]:
            marker.color = default_color_palette[marker.id % len(default_color_palette)]
            await session.commit()

    result = feature_schema.dump(marker)

    await current_app.dispatcher.dispatch_event("features:created",
            "/locations/{}/features/{}".format(location_id, marker.id),
            current=result)

    return jsonify(result), HTTPStatus.CREATED


@features.route('/locations/<uuid:location_id>/features/<int:feature_id>', methods=['DELETE'])
async def delete_feature(location_id, feature_id):
    """
    Delete feature
    ---
    delete:
        summary: Delete feature
        tags:
         - features
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
                        schema: Feature
    """
    async with g.session_maker() as session:
        stmt = sa.select(MapMarker) \
                .where(MapMarker.location_id == location_id) \
                .where(MapMarker.id == feature_id)

        result = await session.execute(stmt)
        marker = result.scalar()
        if marker is None:
            raise exceptions.NotFound(description="Feature {} was not found".format(feature_id))

        await session.delete(marker)
        await session.commit()

    result = feature_schema.dump(marker)

    await current_app.dispatcher.dispatch_event("features:deleted",
            "/locations/{}/features/{}".format(location_id, feature_id),
            previous=result)
    return jsonify(result), HTTPStatus.OK


@features.route('/locations/<uuid:location_id>/features/<int:feature_id>', methods=['GET'])
async def get_feature(location_id, feature_id):
    """
    Get feature
    ---
    get:
        summary: Get feature
        tags:
         - features
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
                        schema: Feature
    """
    async with g.session_maker() as session:
        stmt = sa.select(MapMarker) \
                .where(MapMarker.location_id == location_id) \
                .where(MapMarker.id == feature_id)

        result = await session.execute(stmt)
        marker = result.scalar()
        if marker is None:
            raise exceptions.NotFound(description="Feature {} was not found".format(feature_id))

    result = feature_schema.dump(marker)

    await current_app.dispatcher.dispatch_event("features:viewed",
            "/locations/{}/features/{}".format(location_id, feature_id),
            current=result)

    return jsonify(result), HTTPStatus.OK


@features.route('/locations/<uuid:location_id>/features/<int:feature_id>', methods=['PUT'])
async def replace_feature(location_id, feature_id):
    """
    Replace feature
    ---
    put:
        summary: Replace feature
        tags:
         - features
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Feature
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Feature
    """
    body = await request.get_json()
    if body is None:
        body = {}
    body['id'] = feature_id

    async with g.session_maker() as session:
        stmt = sa.select(MapMarker) \
                .where(MapMarker.location_id == location_id) \
                .where(MapMarker.id == feature_id)

        result = await session.execute(stmt)
        marker = result.scalar()

        if marker is None:
            previous = None
            marker = feature_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
            marker.location_id = location_id
            session.add(marker)
            created = True

        else:
            previous = feature_schema.dump(marker)
            marker.update(body)
            marker.updated_time = datetime.datetime.now()
            created = False

        await session.commit()

    result = feature_schema.dump(marker)

    if created:
        await current_app.dispatcher.dispatch_event("features:created",
                "/locations/{}/features/{}".format(location_id, feature_id),
                current=result, previous=previous)
        return jsonify(result), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("features:updated",
                "/locations/{}/features/{}".format(location_id, feature_id),
                current=result, previous=previous)
        return jsonify(result), HTTPStatus.OK


@features.route('/locations/<uuid:location_id>/features/<int:feature_id>', methods=['PATCH'])
async def update_feature(location_id, feature_id):
    """
    Update feature
    ---
    patch:
        summary: Update feature
        description: This method may be used to modify selected fields of the object.
        tags:
         - features
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Feature
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Feature
    """
    body = await request.get_json()
    if body is None:
        body = {}

    async with g.session_maker() as session:
        stmt = sa.select(MapMarker) \
                .where(MapMarker.location_id == location_id) \
                .where(MapMarker.id == feature_id)

        result = await session.execute(stmt)
        marker = result.scalar()
        if marker is None:
            raise exceptions.NotFound(description="Feature {} was not found".format(feature_id))

        previous = feature_schema.dump(marker)

        marker.update(body)
        marker.updated_time = datetime.datetime.now()
        await session.commit()

    result = feature_schema.dump(marker)

    await current_app.dispatcher.dispatch_event("features:updated",
            "/locations/{}/features/{}".format(location_id, feature_id),
            current=result, previous=previous)
    return jsonify(result), HTTPStatus.OK
