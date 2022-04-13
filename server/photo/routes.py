import os
import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from server.resources.csvresource import CsvCollection

from .models import PhotoModel


photos = Blueprint("photos", __name__)


@photos.route('/photos', methods=['GET'])
async def list_photos():
    """
    List photos
    ---
    get:
        summary: List photos
        tags:
         - photos
    """
    photos = g.active_incident.Photo.find()

    # Wrap the list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): photos}
    else:
        result = photos

    return jsonify(result), HTTPStatus.OK


@photos.route('/photos', methods=['POST'])
async def create_photo():
    """
    Create photo
    ---
    post:
        summary: Create photo
        tags:
         - photos
    """
    body = await request.get_json()

    photo = g.active_incident.Photo.load(body, replace_id=True)

    # The photo object should either specify an external fileUrl, or the caller
    # will need to upload a file after creating this object.
    if photo.fileUrl is None:
        if photo.contentType == "image/jpeg":
            extension = "jpeg"
        elif photo.contentType == "image/png":
            extension = "png"
        else:
            error = "Unsupported content type ({})".format(photo.contentType)
            raise exceptions.BadRequest(description=error)

        upload_file_name = "image.{}".format(extension)
        photo.filePath = os.path.join(photo.get_dir(), upload_file_name)
        photo.fileUrl = "/photos/{}/{}".format(photo.id, upload_file_name)
        photo.status = "created"

    else:
        photo.status = "ready"

    photo.save()

    return jsonify(photo), HTTPStatus.CREATED


@photos.route('/photos/<photo_id>', methods=['DELETE'])
async def delete_photo(photo_id):
    """
    Delete photo
    ---
    delete:
        summary: Delete photo
        tags:
         - photos
    """

    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    photo.delete()

    return jsonify(photo), HTTPStatus.OK


@photos.route('/photos/<photo_id>', methods=['GET'])
async def get_photo(photo_id):
    """
    Get photo
    ---
    get:
        summary: Get photo
        tags:
         - photos
    """
    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    return jsonify(photo), HTTPStatus.OK


@photos.route('/photos/<photo_id>', methods=['PUT'])
async def replace_photo(photo_id):
    """
    Replace photo
    ---
    put:
        summary: Replace photo
        tags:
         - photos
    """
    body = await request.get_json()
    body['id'] = photo_id

    photo = g.active_incident.Photo.load(body)
    created = photo.save()

    if created:
        return jsonify(photo), HTTPStatus.CREATED
    else:
        return jsonify(photo), HTTPStatus.OK


@photos.route('/photos/<photo_id>', methods=['PATCH'])
async def update_photo(photo_id):
    """
    Update photo
    ---
    patch:
        summary: Update photo
        tags:
         - photos
    """

    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    body = await request.get_json()

    # Do not allow changing the object's ID
    if 'id' in body:
        del body['id']

    photo.update(body)
    photo.save()

    return jsonify(photo), HTTPStatus.OK


@photos.route('/photos/<photo_id>/<filename>', methods=['GET'])
async def get_photo_file(photo_id, filename):
    """
    Get a photo data file
    ---
    get:
        summary: Get a photo data file
        tags:
          - photos
        responses:
            200:
                description: The image or other data file.
                content:
                    image/jpeg: {}
                    image/png: {}
    """
    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    data_dir = photo.get_dir()
    return await send_from_directory(data_dir, filename)


@photos.route('/photos/<photo_id>/<filename>', methods=['PUT'])
async def upload_photo_file(photo_id, filename):
    """
    Upload a photo data file
    ---
    put:
        summary: Upload a photo data file
        tags:
          - photos
        requestBody:
            required: true
            content:
                image/jpeg: {}
                image/png: {}
    """
    photo = g.active_incident.Photo.find_by_id(photo_id)
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    file_path = os.path.join(photo.get_dir(), secure_filename(filename))
    created = not os.path.exists(file_path)

    body = await request.get_data()
    with open(file_path, "wb") as output:
        output.write(body)

    photo.filePath = file_path
    photo.fileUrl = "/photos/{}/{}".format(photo_id, secure_filename(filename))
    photo.status = "ready"
    photo.updated = time.time()
    photo.save()

    if created:
        return jsonify(photo), HTTPStatus.CREATED
    else:
        return jsonify(photo), HTTPStatus.OK
