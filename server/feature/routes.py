import os
import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from .models import FeatureModel


features = Blueprint("features", __name__)


@features.route('/locations/<location_id>/features', methods=['GET'])
async def list_features(location_id):
    """
    List features
    ---
    get:
        summary: List features
        tags:
         - features
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    features = location.Feature.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): features}
    else:
        result = features

    return jsonify(result), HTTPStatus.OK


@features.route('/locations/<location_id>/features', methods=['POST'])
async def create_feature(location_id):
    """
    Create feature
    ---
    post:
        summary: Create feature
        tags:
         - features
    """
    body = await request.get_json()

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    feature = location.Feature.load(body, replace_id=True)
    feature.save()

    return jsonify(feature), HTTPStatus.CREATED


@features.route('/locations/<location_id>/features/<feature_id>', methods=['DELETE'])
async def delete_feature(location_id, feature_id):
    """
    Delete feature
    ---
    delete:
        summary: Delete feature
        tags:
         - features
    """

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    feature = location.Feature.find_by_id(feature_id)
    if feature is None:
        raise exceptions.NotFound(description="Feature {} was not found".format(feature_id))

    feature.delete()

    return jsonify(feature), HTTPStatus.OK


@features.route('/locations/<location_id>/features/<feature_id>', methods=['GET'])
async def get_feature(location_id, feature_id):
    """
    Get feature
    ---
    get:
        summary: Get feature
        tags:
         - features
    """
    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    feature = location.Feature.find_by_id(feature_id)
    if feature is None:
        raise exceptions.NotFound(description="Feature {} was not found".format(feature_id))

    return jsonify(feature), HTTPStatus.OK


@features.route('/locations/<location_id>/features/<feature_id>', methods=['PUT'])
async def replace_feature(location_id, feature_id):
    """
    Replace feature
    ---
    put:
        summary: Replace feature
        tags:
         - features
    """
    body = await request.get_json()
    body['id'] = feature_id

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    feature = location.Feature.load(body)
    created = feature.save()

    if created:
        return jsonify(feature), HTTPStatus.CREATED
    else:
        return jsonify(feature), HTTPStatus.OK


@features.route('/locations/<location_id>/features/<feature_id>', methods=['PATCH'])
async def update_feature(location_id, feature_id):
    """
    Update feature
    ---
    patch:
        summary: Update feature
        tags:
         - features
    """

    location = g.active_incident.Location.find_by_id(location_id)
    if location is None:
        raise exceptions.NotFound(description="Location {} was not found".format(location_id))

    feature = location.Feature.find_by_id(feature_id)
    if feature is None:
        raise exceptions.NotFound(description="Feature {} was not found".format(feature_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    feature.update(body)
    feature.save()

    return jsonify(feature), HTTPStatus.OK
