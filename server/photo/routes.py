import asyncio
import os
import time

from http import HTTPStatus

from quart import Blueprint, g, jsonify, request, send_from_directory
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from server.resources.csvresource import CsvCollection
from server.resources.filter import Filter
from server.utils.utils import save_image

from .models import PhotoModel


photos = Blueprint("photos", __name__)


def get_photo_extension(photo):
    if photo.contentType == "image/jpeg":
        return "jpeg"
    elif photo.contentType == "image/png":
        return "png"
    else:
        error = "Unsupported content type ({})".format(photo.contentType)
        raise exceptions.BadRequest(description=error)


@photos.route('/photos', methods=['GET'])
async def list_photos():
    """
    List photos
    ---
    get:
        summary: List photos
        tags:
         - photos
        parameters:
          - name: envelope
            in: query
            required: false
            schema:
                type: str
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: ready
            in: query
            required: false
            schema:
                type: boolean
            description: Only show items with ready flag set.
          - name: since
            in: query
            required: false
            schema:
                type: float
            description: Only show items that were created or updated since this time.
          - name: until
            in: query
            required: false
            schema:
                type: float
            description: Only show items that were created or updated before this time.
          - name: wait
            in: query
            required: false
            schema:
                type: float
            description: >-
                Request that the server wait a time limit (in seconds) for a
                new result if none are immediately available. The server will
                return one or more results as soon as they are available, or if
                the time limit has passed, the server will return a No Content
                204 result indicating timeout. A time limit of 30-60 seconds is
                recommended.
        responses:
            200:
                description: A list of objects.
                content:
                    application/json:
                        schema:
                            type: array
                            items: Photo
    """
    filt = Filter()
    if "ready" in request.args:
        filt.target_equal_to("ready", True)
    if "since" in request.args:
        filt.target_greater_than("updated", float(request.args.get("since")))
    if "until" in request.args:
        filt.target_less_than("updated", float(request.args.get("until")))

    items = g.active_incident.Photo.find(filt=filt)

    # Wait for new objects if the query returned no results and the caller
    # specified a wait timeout. If there are still no results, we return a 204
    # No Content code.
    wait = float(request.args.get("wait", 0))
    if len(items) == 0 and wait > 0:
        try:
            item = await asyncio.wait_for(g.active_incident.Photo.wait_for(filt=filt), timeout=wait)
            items.append(item)
        except asyncio.TimeoutError:
            return jsonify([]), HTTPStatus.NO_CONTENT

    # Wrap the list if the caller requested an envelope.
    if "envelope" in request.args:
        result = {request.args.get("envelope"): items}
    else:
        result = items

    return jsonify(result), HTTPStatus.OK


@photos.route('/photos', methods=['POST'])
async def create_photo():
    """
    Create photo
    ---
    post:
        summary: Create photo
        description: |-
            This method may be used to link to an external image simply by
            setting the imageUrl in the request body, but for its intended use
            case, it is the first step to initiate an image upload to the edge
            server.

            The following example starts the upload process by sending some
            basic information about the image to the edge server.

                POST /photos
                Content-Type: application/json
                {
                    "contentType": "image/jpeg",
                    "width": 640,
                    "height": 480,
                    "cameraPosition": {"x": 0, "y": 0, "z": 0},
                    "cameraOrientation": {"x": 0, "y": 0, "z": 0, "w": 0}
                }

            The server responds with the new photo record, which most importantly,
            contains the location for the image URL. The ready flag will change from
            false to true after the client completes the image upload.

                201 CREATED
                Content-Type: application/json
                {
                    "id": "53c08f93-93b6-4f7c-b9a4-676b5e37b744",
                    "imageUrl": "/photos/53c08f93-93b6-4f7c-b9a4-676b5e37b744/image.jpeg",
                    "ready": false,
                    ...
                }

            The client can use the information from the server's response to complete
            the image upload using the imageUrl returned by the server.

                PUT /photos/53c08f93-93b6-4f7c-b9a4-676b5e37b744/image.jpeg
                Content-Type: image/jpeg
                [ DATA ]
        tags:
         - photos
        requestBody:
            required: true
            content:
                application/json:
                    schema: Photo
        responses:
            201:
                description: The created object
                content:
                    application/json:
                        schema: Photo
    """
    body = await request.get_json()

    photo = g.active_incident.Photo.load(body, replace_id=True)

    # The photo object should either specify an external imageUrl, or the caller
    # will need to upload a file after creating this object.
    if photo.imageUrl is None or photo.imageUrl.strip() == "":
        upload_file_name = "image.{}".format(get_photo_extension(photo))
        photo.imagePath = os.path.join(photo.get_dir(), upload_file_name)
        photo.imageUrl = "/photos/{}/image".format(photo.id)
        photo.ready = False

    else:
        photo.ready = True

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
                        schema: Photo
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
                        schema: Photo
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
        parameters:
          - name: id
            in: path
            required: true
            description: The object ID
        requestBody:
            required: true
            content:
                application/json:
                    schema: Photo
        responses:
            200:
                description: The new object
                content:
                    application/json:
                        schema: Photo
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
        description: |-
            This method may be used to modify selected fields of the object.

            The following example would annotate the photo which has ID 0 to
            note a detected fire extinguisher in the image, expressed as a
            relative position and size. Please be aware that this would
            overwrite any existing annotation.

                PATCH /photos/0
                Content-Type: application/json
                {
                    "width": 640,
                    "height": 480,
                    "annotations": [{
                        "label": "extinguisher",
                        "confidence": 1.0,
                        "boundary": {
                            "left": 0.1,
                            "top": 0.1,
                            "width": 0.5,
                            "height": 0.5
                        }
                    }]
                }
        tags:
         - photos
        parameters:
          - name: id
            in: path
            required: true
            description: ID of the object to be modified
        requestBody:
            required: true
            content:
                application/json:
                    schema: Photo
        responses:
            200:
                description: The modified object
                content:
                    application/json:
                        schema: Photo
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


@photos.route('/photos/<photo_id>/image', methods=['GET'])
async def get_photo_file(photo_id):
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

    return await send_from_directory(photo.get_dir(), os.path.basename(photo.imagePath))


@photos.route('/photos/<photo_id>/image', methods=['PUT'])
async def upload_photo_file(photo_id):
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

    # In case the image path was not set correctly or even was set maliciously,
    # reconstruct it here before writing the file.
    upload_file_name = "image.{}".format(get_photo_extension(photo))
    photo.imagePath = os.path.join(photo.get_dir(), upload_file_name)

    created = not os.path.exists(photo.imagePath)

    request_files = await request.files
    if 'image' in request_files:
        await save_image(photo.imagePath, request_files['image'])
    else:
        body = await request.get_data()
        with open(photo.imagePath, "wb") as output:
            output.write(body)

    photo.imageUrl = "/photos/{}/image".format(photo_id)
    photo.ready = True
    photo.updated = time.time()
    photo.save()

    if created:
        return jsonify(photo), HTTPStatus.CREATED
    else:
        return jsonify(photo), HTTPStatus.OK
