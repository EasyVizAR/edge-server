import asyncio
import os
import time

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from PIL import Image

from server.resources.csvresource import CsvCollection
from server.resources.filter import Filter
from server.utils.rate_limiter import rate_limit_exempt
from server.utils.utils import save_image

from .cleanup import PhotoCleanupTask
from .models import PhotoFile, PhotoModel


photos = Blueprint("photos", __name__)

# Interval for purging temporary photos (in seconds)
cleanup_interval = 300

thumbnail_max_size = (320, 320)


def get_photo_extension(photo):
    if photo.contentType == "image/jpeg":
        return "jpeg"
    elif photo.contentType == "image/png":
        return "png"
    else:
        error = "Unsupported content type ({})".format(photo.contentType)
        raise exceptions.BadRequest(description=error)


def schedule_cleanup():
    if time.time() - current_app.last_photo_cleanup >= cleanup_interval:
        task = PhotoCleanupTask(g.active_incident.id)
        current_app.thread_pool.submit(task.run)
        current_app.last_photo_cleanup = time.time()


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
          - name: camera_location_id
            in: query
            required: false
            schema:
                type: str
            description: Only show items with the specified location ID.
          - name: created_by
            in: query
            required: false
            schema:
                type: str
            description: Only show items created by the specified headset ID.
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
          - name: retention
            in: query
            required: false
            schema:
                type: str
            description: Only show items with specified retention policy (auto|temporary|permanent).
          - name: since
            in: query
            required: false
            schema:
                type: float
            description: Only show items that were created or updated since this time.
          - name: status
            in: query
            required: false
            schema:
                type: str
            description: Only show items with specified status.
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
    if "camera_location_id" in request.args:
        filt.target_equal_to("camera_location_id", request.args.get("camera_location_id"))
    if "created_by" in request.args:
        filt.target_equal_to("created_by", request.args.get("created_by"))
    if "ready" in request.args:
        filt.target_equal_to("ready", True)
    if "retention" in request.args:
        filt.target_equal_to("retention", request.args.get("retention"))
    if "since" in request.args:
        filt.target_greater_than("updated", float(request.args.get("since")))
    if "status" in request.args:
        filt.target_equal_to("status", request.args.get("status"))
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

    await current_app.dispatcher.dispatch_event("photos:viewed", "/photos")
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
                    "camera_location_id": "66a4e9f2-e978-4405-988e-e168a9429030",
                    "camera_position": {"x": 0, "y": 0, "z": 0},
                    "camera_orientation": {"x": 0, "y": 0, "z": 0, "w": 0}
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
                    "status": "created",
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
        photo.status = "created"

    else:
        photo.ready = True
        photo.status = "ready"

    photo.save()
    schedule_cleanup()

    await current_app.dispatcher.dispatch_event("photos:created",
            "/photos/"+photo.id, current=photo)
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

    await current_app.dispatcher.dispatch_event("photos:deleted",
            "/photos/"+photo.id, previous=photo)
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
          - name: status
            in: query
            required: false
            schema:
                type: str
            description: Only return when the status matches this value
          - name: wait
            in: query
            required: false
            schema:
                type: float
            description: >-
                Request that the server wait a time limit (in seconds) for the
                result if it is not ready. This can be used to wait until a
                photo is done processing by also requesting status=done. If the
                time limit has passed without a result, the server will return
                a No Content 204 result. A time limit of 30-60 seconds is
                recommended in order to work reliably with any other timeouts
                that may apply.
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

    filt = Filter()
    filt.target_equal_to("id", photo_id)
    if "status" in request.args:
        filt.target_equal_to("status", request.args.get("status"))

    # Wait for new objects if the query returned no results and the caller
    # specified a wait timeout. If there are still no results, we return a 204
    # No Content code.
    wait = float(request.args.get("wait", 0))
    if not filt.matches(photo) and wait > 0:
        try:
            photo = await asyncio.wait_for(g.active_incident.Photo.wait_for(filt=filt), timeout=wait)
        except asyncio.TimeoutError:
            return jsonify([]), HTTPStatus.NO_CONTENT

    await current_app.dispatcher.dispatch_event("photos:viewed",
            "/photos/"+photo.id, current=photo)
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

    previous = g.active_incident.Photo.find_by_id(photo_id)
    photo = g.active_incident.Photo.load(body)
    created = photo.save()

    if created:
        await current_app.dispatcher.dispatch_event("photos:created",
                "/photos/"+photo.id, current=photo)
        return jsonify(photo), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("photos:updated",
                "/photos/"+photo.id, current=photo, previous=previous)
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

    previous = g.active_incident.Photo.find_by_id(photo_id)
    photo.update(body)
    photo.save()

    await current_app.dispatcher.dispatch_event("photos:updated",
            "/photos/"+photo.id, current=photo, previous=previous)
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


@photos.route('/photos/<photo_id>/thumbnail', methods=['GET'])
@rate_limit_exempt
async def get_photo_thumbnail(photo_id):
    """
    Get a photo thumbnail file
    ---
    get:
        summary: Get a photo thumbnail file
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

    thumbnail_file = "thumbnail."+get_photo_extension(photo)
    thumbnail_path = os.path.join(photo.get_dir(), thumbnail_file)
    if not os.path.exists(thumbnail_path):
        original_path = os.path.join(photo.imagePath)
        with Image.open(original_path) as im:
            im.thumbnail(thumbnail_max_size)
            im.save(thumbnail_path, im.format)

    return await send_from_directory(photo.get_dir(), os.path.basename(thumbnail_file))


@photos.route('/photos/<photo_id>/<filename>', methods=['GET'])
async def get_photo_file_by_name(photo_id, filename):
    """
    Get a photo file by name
    ---
    get:
        summary: Get a photo file by name
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

    return await send_from_directory(photo.get_dir(), secure_filename(filename))


def process_uploaded_photo_file(photo, upload_file_path, upload_file_name, file_purpose):
    with Image.open(upload_file_path) as image:
        content_type = "image/{}".format(image.format.lower())

        photo.files.append(PhotoFile(upload_file_name, file_purpose,
            width = image.width,
            height = image.height,
            content_type = content_type
        ))

        if file_purpose == "photo":
            photo.imagePath = upload_file_path
            photo.width = image.width
            photo.height = image.height
            photo.contentType = content_type

            # If the photo exceeds the thumbnail size, then generate a smaller
            # thumbnail version.  Otherwise, there is no need to make a thumbnail.
            if photo.width > thumbnail_max_size[0] or photo.height > thumbnail_max_size[1]:
                thumbnail_file = "thumbnail."+get_photo_extension(photo)
                thumbnail_path = os.path.join(photo.get_dir(), thumbnail_file)
                image.thumbnail(thumbnail_max_size)
                image.save(thumbnail_path, image.format)

                photo.files.append(PhotoFile(thumbnail_file, "thumbnail",
                    width = image.width,
                    height = image.height,
                    content_type = photo.contentType
                ))


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

    try:
        process_uploaded_photo_file(photo, photo.imagePath, upload_file_name, "photo")
    except:
        pass

    previous = g.active_incident.Photo.find_by_id(photo_id)
    photo.imageUrl = "/photos/{}/image".format(photo_id)
    photo.ready = True
    photo.status = "ready"
    photo.updated = time.time()
    photo.save()

    if created:
        await current_app.dispatcher.dispatch_event("photos:created",
                "/photos/"+photo.id, current=photo)
        return jsonify(photo), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("photos:updated",
                "/photos/"+photo.id, current=photo, previous=previous)
        return jsonify(photo), HTTPStatus.OK


@photos.route('/photos/<photo_id>/<filename>', methods=['PUT'])
async def upload_photo_file_by_name(photo_id, filename):
    """
    Upload a photo file by name
    ---
    put:
        summary: Upload a photo file by name
        description: |-
            This method may be used to upload primary and secondary image
            files.  Here, primary refers to an ordinary color camera image.
            Secondary files may be thumbnail images, view space geometry
            images, thermal images, etc. The filename in the path should match
            one of the supported use cases (photo|depth|geometry|thermal|thumbnail).
            This currently assumes that only one of each type will be uploaded.

            Example:

                PUT /photos/5b737da7-1363-4072-9bc3-c96faf974b1a/photo.png
                    -> upload a primary photo

                PUT /photos/5b737da7-1363-4072-9bc3-c96faf974b1a/geometry.png
                    -> upload a geometry image
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
    upload_file_name = secure_filename(filename)
    upload_file_path = os.path.join(photo.get_dir(), upload_file_name)
    file_purpose, file_ext = os.path.splitext(upload_file_name)
    file_purpose = file_purpose.lower()

    created = not os.path.exists(upload_file_path)

    request_files = await request.files
    if 'image' in request_files:
        await save_image(upload_file_path, request_files['image'])
    else:
        body = await request.get_data()
        with open(upload_file_path, "wb") as output:
            output.write(body)

    try:
        process_uploaded_photo_file(photo, upload_file_path, upload_file_name, file_purpose)
    except:
        pass

    previous = g.active_incident.Photo.find_by_id(photo_id)
    photo.imageUrl = "/photos/{}/image".format(photo_id)
    if file_purpose == "photo":
        photo.ready = True
        photo.status = "ready"
    photo.updated = time.time()
    photo.save()

    if created:
        await current_app.dispatcher.dispatch_event("photos:created",
                "/photos/"+photo.id, current=photo)
        return jsonify(photo), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("photos:updated",
                "/photos/"+photo.id, current=photo, previous=previous)
        return jsonify(photo), HTTPStatus.OK
