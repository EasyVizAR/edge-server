
from http import HTTPStatus

from quart import Blueprint, g, jsonify, request
from werkzeug import exceptions


annotations = Blueprint("annotations", __name__)


@annotations.route('/photos/<photo_id>/annotations', methods=['GET'])
async def list_annotations(photo_id):
    """
    List annotations
    ---
    get:
        summary: List annotations
        tags:
         - annotations
        parameters:
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
        responses:
            200:
                description: A list of annotations.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Annotation
    """
    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    annotations = photo.Annotation.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): annotations}
    else:
        result = annotations

    return jsonify(result), HTTPStatus.OK


@annotations.route('/photos/<photo_id>/annotations', methods=['POST'])
async def create_annotation(photo_id):
    """
    Create annotation
    ---
    post:
        summary: Create annotation
        tags:
         - annotations
        requestBody:
            required: true
            content:
                application/json:
                    schema: Annotation
        responses:
            200:
                description: An annotation object
                content:
                    application/json:
                        schema: Annotation
    """
    body = await request.get_json()

    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    annotation = photo.Annotation.load(body, replace_id=True)
    annotation.save()

    return jsonify(annotation), HTTPStatus.CREATED


@annotations.route('/photos/<photo_id>/annotations/<annotation_id>', methods=['DELETE'])
async def delete_annotation(photo_id, annotation_id):
    """
    Delete annotation
    ---
    delete:
        summary: Delete annotation
        tags:
         - annotations
        parameters:
          - name: id
            in: path
            required: true
            description: Annotation ID
        responses:
            200:
                description: The object which was deleted
                content:
                    application/json:
                        schema: Annotation
    """

    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    annotation = photo.Annotation.find_by_id(annotation_id)
    if annotation is None:
        raise exceptions.NotFound(description="Annotation {} was not found".format(annotation_id))

    annotation.delete()

    return jsonify(annotation), HTTPStatus.OK


@annotations.route('/photos/<photo_id>/annotations/<annotation_id>', methods=['GET'])
async def get_annotation(photo_id, annotation_id):
    """
    Get annotation
    ---
    get:
        summary: Get annotation
        tags:
         - annotations
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
                        schema: Annotation
    """
    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    annotation = photo.Annotation.find_by_id(annotation_id)
    if annotation is None:
        raise exceptions.NotFound(description="Annotation {} was not found".format(annotation_id))

    return jsonify(annotation), HTTPStatus.OK


@annotations.route('/photos/<photo_id>/annotations/<annotation_id>', methods=['PUT'])
async def replace_annotation(photo_id, annotation_id):
    """
    Replace annotation
    ---
    put:
        summary: Replace annotation
        tags:
         - annotations
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Annotation
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Annotation
    """
    body = await request.get_json()
    body['id'] = annotation_id

    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    annotation = photo.Annotation.load(body)
    created = annotation.save()

    if created:
        return jsonify(annotation), HTTPStatus.CREATED
    else:
        return jsonify(annotation), HTTPStatus.OK


@annotations.route('/photos/<photo_id>/annotations/<annotation_id>', methods=['PATCH'])
async def update_annotation(photo_id, annotation_id):
    """
    Update annotation
    ---
    patch:
        summary: Update annotation
        description: This method may be used to modify selected fields of the object.
        tags:
         - annotations
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Annotation
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Annotation
    """

    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    annotation = photo.Annotation.find_by_id(annotation_id)
    if annotation is None:
        raise exceptions.NotFound(description="Annotation {} was not found".format(annotation_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    annotation.update(body)
    annotation.save()

    return jsonify(annotation), HTTPStatus.OK
