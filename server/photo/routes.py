import asyncio
import datetime
import os
import shutil
import time
import uuid

from http import HTTPStatus

from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug import exceptions
from werkzeug.utils import secure_filename

from PIL import Image

import marshmallow
import sqlalchemy as sa

from server import auth
from server.models.mobile_devices import MobileDevice
from server.resources.filter import Filter
from server.utils.images import assemble_patches, ext_from_type
from server.utils.rate_limiter import rate_limit_exempt
from server.utils.utils import save_image
from server.utils.response import maybe_wrap

from .cleanup import PhotoCleanupTask
from .models import PhotoFile, PhotoRecord, DetectionTaskSchema, PhotoAnnotationSchema, PhotoSchema


photos = Blueprint("photos", __name__)

photo_schema = PhotoSchema()
detection_task_schema = DetectionTaskSchema()
photo_annotation_schema = PhotoAnnotationSchema()

# Interval for purging temporary photos (in seconds)
cleanup_interval = 300

thumbnail_max_size = (320, 320)


def get_photo_dir(location_id, photo_id):
    return os.path.join(g.data_dir, 'locations', location_id.hex, 'photos', '{:08x}'.format(photo_id))


def get_transient_photo_dir(location_id):
    return os.path.join(g.data_dir, 'locations', location_id.hex, 'transient_photos')


def get_timestamp():
    return int(100000 * time.time())


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
          - name: queue_name
            in: query
            required: false
            schema:
                type: str
            description: Only show items in the specified queue.
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
    items = []
    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord)

        try:
            camera_location_id = uuid.UUID(request.args.get('camera_location_id'))
            stmt = stmt.where(PhotoRecord.location_id == camera_location_id)
        except:
            pass

        try:
            created_by = uuid.UUID(request.args.get('created_by'))
            stmt = stmt.where(PhotoRecord.mobile_device_id == created_by)
        except:
            pass

        queue_name = request.args.get("queue_name")
        if queue_name is not None:
            stmt = stmt.where(PhotoRecord.queue_name == queue_name)

        since = request.args.get('since')
        if since is not None:
            stmt = stmt.where(PhotoRecord.updated_time > since)

        until = request.args.get('until')
        if until is not None:
            stmt = stmt.where(PhotoRecord.updated_time < until)

        stmt = stmt.options(sa.orm.selectinload(PhotoRecord.annotations))
        stmt = stmt.options(sa.orm.selectinload(PhotoRecord.files))
        stmt = stmt.options(sa.orm.selectinload(PhotoRecord.pose))

        result = await session.execute(stmt)
        for row in result.scalars():
            items.append(photo_schema.dump(row))

    # Wait for new objects if the query returned no results and the caller
    # specified a wait timeout. If there are still no results, we return a 204
    # No Content code.
#    wait = float(request.args.get("wait", 0))
#    if len(items) == 0 and wait > 0:
#        try:
#            item = await asyncio.wait_for(g.active_incident.Photo.wait_for(filt=filt), timeout=wait)
#            items.append(item)
#        except asyncio.TimeoutError:
#            return jsonify([]), HTTPStatus.NO_CONTENT

    await current_app.dispatcher.dispatch_event("photos:viewed", "/photos")
    return jsonify(maybe_wrap(items)), HTTPStatus.OK


async def create_photo_entry(body):
    # The caller should not be sending an ID, but check and dismiss it.
    if 'id' in body:
        del body['id']

    photo = photo_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
    photo.queue_name = "created"
    photo.annotations = []
    photo.files = []

    if photo.incident_id is None:
        photo.incident_id = g.active_incident_id

    if g.device_id is not None:
        photo.mobile_device_id = g.device_id

        device = await g.session.get(MobileDevice, g.device_id)
        if device is not None:
            photo.location_id = device.location_id
            photo.tracking_session_id = device.tracking_session_id
            photo.device_pose_id = device.device_pose_id

    g.session.add(photo)
    await g.session.commit()

    return photo


async def save_upload_to_file(path):
    request_files = await request.files
    if 'image' in request_files:
        await request_files['image'].save(path)
    elif 'patches' in request_files:
        patches = request_files.getlist("patches")
        path = await assemble_patches(patches, path)
    else:
        body = await request.get_data()
        with open(path, "wb") as output:
            output.write(body)
    return path


async def create_photo_quick():
    device = await g.session.get(MobileDevice, g.device_id)
    if device is None:
        raise exceptions.Unauthorized("Device not authenticated")

    photo = PhotoRecord(
            incident_id=g.active_incident_id,
            mobile_device_id=device.id,
            location_id=device.location_id,
            tracking_session_id=device.tracking_session_id,
            device_pose_id=device.device_pose_id,
            queue_name=request.headers.get("X-Queue-Name", "detection"),
    )
    g.session.add(photo)
    await g.session.flush()

    photo_dir = get_photo_dir(photo.location_id, photo.id)
    os.makedirs(photo_dir, exist_ok=True)

    temp_filename = "image-{}-{}".format(photo.location_id.hex, photo.id)
    temp_path = os.path.join(g.temp_dir, temp_filename)
    temp_path = await save_upload_to_file(temp_path)

    photo_type = current_app.magic.from_file(temp_path)
    photo_filename = "photo" + ext_from_type(photo_type)
    photo_path = os.path.join(photo_dir, photo_filename)
    shutil.move(temp_path, photo_path)

    photo_file = PhotoFile(
            name=photo_filename,
            photo_record_id=photo.id,
            purpose="photo",
            content_type=photo_type
    )

    try:
        with Image.open(photo_path) as im:
            photo_file.content_type = im.get_format_mimetype()
            photo_file.width = im.width
            photo_file.height = im.height
    except:
        pass

    g.session.add(photo_file)
    await g.session.commit()

    # We are done with database interactions.  Making the object transient
    # allows us to set up the nested fields without attempting to write back to
    # the database.
    sa.orm.make_transient(photo)
    photo.annotations = []
    photo.files = [photo_file]

    return photo


async def create_photo_transient():
    location_id = uuid.UUID(request.headers.get("X-Location-Id"))
    photo_dir = get_transient_photo_dir(location_id)
    os.makedirs(photo_dir, exist_ok=True)

    content_type = request.headers.get("Content-Type")
    photo_filename = "{}{}".format(get_timestamp(), ext_from_type(content_type))
    photo_path = os.path.join(photo_dir, photo_filename)

    photo_path = await save_upload_to_file(photo_path)


@photos.route('/photos', methods=['POST'])
@rate_limit_exempt
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
    storage = request.headers.get("X-Storage", "normal")
    if storage == "transient":
        await create_photo_transient()
        return "", HTTPStatus.CREATED

    # If the POST request contains JSON, we simply create the photo record.
    # The caller can then use the newly created photo ID to upload the actual
    # image(s).
    if request.is_json:
        body = await request.get_json()
        photo = await create_photo_entry(body)

    # Otherwise, we permit directly uploading an image and creating a record
    # for it. This may reduce upload latency but gives the caller less
    # flexibility in setting metadata associated with the photo.
    else:
        photo = await create_photo_quick()

    result = photo_schema.dump(photo)

    await current_app.dispatcher.dispatch_event("photos:created",
            "/photos/"+str(photo.id), current=result)
    return jsonify(result), HTTPStatus.CREATED


@photos.route('/photos/<int:photo_id>', methods=['DELETE'])
@auth.requires_admin
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
    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.id == photo_id) \
                .limit(1)

        result = await session.execute(stmt)
        photo = result.scalar()
        if photo is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

        await session.delete(photo)
        await session.commit()

    result = photo_schema.dump(photo)

    await current_app.dispatcher.dispatch_event("photos:deleted",
            "/photos/"+str(photo.id), previous=result)

    return jsonify(result), HTTPStatus.OK


@photos.route('/photos/<int:photo_id>', methods=['GET'])
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
    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.id == photo_id) \
                .limit(1) \
                .options(sa.orm.selectinload(PhotoRecord.annotations)) \
                .options(sa.orm.selectinload(PhotoRecord.files)) \
                .options(sa.orm.selectinload(PhotoRecord.pose))

        result = await session.execute(stmt)
        photo = result.scalar()
        if photo is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    result = photo_schema.dump(photo)

    await current_app.dispatcher.dispatch_event("photos:viewed",
            "/photos/"+str(photo.id), current=result)

    return jsonify(result), HTTPStatus.OK


@photos.route('/photos/<int:photo_id>', methods=['PUT'])
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
    if body is None:
        body = {}
    body['id'] = photo_id

    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.id == photo_id) \
                .limit(1) \
                .options(sa.orm.selectinload(PhotoRecord.annotations)) \
                .options(sa.orm.selectinload(PhotoRecord.files))

        result = await session.execute(stmt)
        photo = result.scalar()

        if photo is None:
            previous = None
            photo = photo_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
            if photo.incident_id is None:
                photo.incident_id = g.active_incident_id
            session.add(photo)
            created = True

        else:
            previous = photo_schema.dump(photo)
            photo.update(body)
            photo.updated_time = datetime.datetime.now()
            created = False

        await session.commit()

    result = photo_schema.dump(photo)

    if created:
        await current_app.dispatcher.dispatch_event("photos:created",
                "/photos/"+str(photo.id), current=result)
        return jsonify(result), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("photos:updated",
                "/photos/"+str(photo.id), current=result, previous=previous)
        return jsonify(result), HTTPStatus.OK


@photos.route('/photos/<int:photo_id>', methods=['PATCH'])
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
    body = await request.get_json()

    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.id == photo_id) \
                .limit(1) \
                .options(sa.orm.selectinload(PhotoRecord.annotations)) \
                .options(sa.orm.selectinload(PhotoRecord.files))

        result = await session.execute(stmt)
        photo = result.scalar()
        if photo is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

        previous = photo_schema.dump(photo)
        photo.update(body)
        photo.updated_time = datetime.datetime.now()

        # Support creating photo annotations through patching the photo record
        if "annotations" in body:
            detection_task = detection_task_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
            detection_task.photo_record_id = photo_id
            session.add(detection_task)
            await session.flush()

            photo.annotations = []

            for item in body['annotations']:
                annotation = photo_annotation_schema.load(item, transient=True)
                annotation.photo_record_id = photo_id
                annotation.detection_task_id = detection_task.id
                session.add(annotation)
                photo.annotations.append(annotation)

        # Support older clients that set a status flag
        if body.get("status") is not None:
            photo.queue_name = body.get("status")

        await session.commit()

    result = photo_schema.dump(photo)

    await current_app.dispatcher.dispatch_event("photos:updated",
            "/photos/"+str(photo.id), current=result, previous=previous)

    return jsonify(result), HTTPStatus.OK


@photos.route('/photos/<int:photo_id>/image', methods=['GET'])
@rate_limit_exempt
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
    async with g.session_maker() as session:
        stmt = sa.select(PhotoFile) \
                .where(PhotoFile.photo_record_id == photo_id) \
                .where(PhotoFile.purpose == "photo") \
                .limit(1) \
                .options(sa.orm.selectinload(PhotoFile.record))

        result = await session.execute(stmt)
        photo = result.scalar()
        if photo is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

        photo_dir = get_photo_dir(photo.record.location_id, photo_id)

    return await send_from_directory(photo_dir, photo.name)


@photos.route('/photos/<int:photo_id>/thumbnail', methods=['GET'])
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
    async with g.session_maker() as session:
        stmt = sa.select(PhotoFile) \
                .where(PhotoFile.photo_record_id == photo_id) \
                .options(sa.orm.selectinload(PhotoFile.record))

        photo = None
        thumbnail = None

        result = await session.execute(stmt)
        for row in result.scalars():
            if row.purpose == "photo":
                photo = row
            elif row.purpose == "thumbnail":
                thumbnail = row

        if photo is None and thumbnail is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

        photo_dir = get_photo_dir(photo.record.location_id, photo_id)

        if thumbnail is None:
            thumbnail = PhotoFile(
                    name="thumbnail.png",
                    photo_record_id=photo_id,
                    purpose="thumbnail",
                    content_type="image/png"
            )

            with Image.open(os.path.join(photo_dir, photo.name)) as im:
                im.thumbnail(thumbnail_max_size)
                im.save(os.path.join(photo_dir, thumbnail.name))

                thumbnail.width = im.width
                thumbnail.height = im.height

            session.add(thumbnail)
            await session.commit()

    return await send_from_directory(photo_dir, thumbnail.name)


@photos.route('/photos/<int:photo_id>/<filename>', methods=['GET'])
@rate_limit_exempt
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
    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.id == photo_id) \
                .limit(1)

        result = await session.execute(stmt)
        photo = result.scalar()
        if photo is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    photo_dir = get_photo_dir(photo.location_id, photo_id)
    return await send_from_directory(photo_dir, secure_filename(filename))


@photos.route('/photos/<int:photo_id>/image', methods=['PUT'])
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
    async with g.session_maker() as session:
        stmt = sa.select(PhotoRecord) \
                .where(PhotoRecord.id == photo_id) \
                .limit(1) \
                .options(sa.orm.selectinload(PhotoRecord.annotations)) \
                .options(sa.orm.selectinload(PhotoRecord.files))

        result = await session.execute(stmt)
        photo = result.scalar()
        if photo is None:
            raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

        previous = photo_schema.dump(photo)

        photo_dir = get_photo_dir(photo.location_id, photo_id)
        os.makedirs(photo_dir, exist_ok=True)

        photo_file = None
        for file in photo.files:
            if file.purpose == "photo":
                photo_file = file
                break

        if photo_file is None:
            photo_file = PhotoFile(
                name="photo.png",
                photo_record_id=photo_id,
                purpose="photo",
                content_type="image/png"
            )
            session.add(photo_file)
            photo.files.append(photo_file)
            created = True
        else:
            created = False

        photo_path = os.path.join(photo_dir, photo_file.name)
        photo_path = await save_upload_to_file(photo_path)

        try:
            with Image.open(photo_path) as im:
                photo_file.content_type = im.get_format_mimetype()
                photo_file.width = im.width
                photo_file.height = im.height
        except:
            pass

        photo.queue_name = "detection"
        photo.updated_time = datetime.datetime.now()
        photo_file.updated_time = datetime.datetime.now()

        await session.commit()

    result = photo_schema.dump(photo)

    if created:
        await current_app.dispatcher.dispatch_event("photos:created",
                "/photos/"+str(photo_id), current=result)
        return jsonify(result), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("photos:updated",
                "/photos/"+str(photo_id), current=result, previous=previous)
        return jsonify(result), HTTPStatus.OK


@photos.route('/photos/<int:photo_id>/<filename>', methods=['PUT'])
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
    stmt = sa.select(PhotoRecord) \
            .where(PhotoRecord.id == photo_id) \
            .limit(1) \
            .options(sa.orm.selectinload(PhotoRecord.annotations)) \
            .options(sa.orm.selectinload(PhotoRecord.files))

    result = await g.session.execute(stmt)
    photo = result.scalar()
    if photo is None:
        raise exceptions.NotFound(description="Photo {} was not found".format(photo_id))

    previous = photo_schema.dump(photo)

    photo_dir = get_photo_dir(photo.location_id, photo_id)
    os.makedirs(photo_dir, exist_ok=True)

    upload_file_name = secure_filename(filename)

    stmt = sa.select(PhotoFile) \
            .where(PhotoFile.photo_record_id == photo_id) \
            .where(PhotoFile.name == upload_file_name) \
            .limit(1)

    result = await g.session.execute(stmt)
    file = result.scalar()

    if file is None:
        file_purpose, file_ext = os.path.splitext(upload_file_name)
        file_purpose = file_purpose.lower()

        file = PhotoFile(
            name=upload_file_name,
            photo_record_id=photo_id,
            purpose=file_purpose,
            content_type="image/png"
        )
        g.session.add(file)
        created = True
    else:
        created = False

    photo_path = os.path.join(photo_dir, upload_file_name)
    photo_path = await save_upload_to_file(photo_path)

    try:
        with Image.open(photo_path) as im:
            file.content_type = im.get_format_mimetype()
            file.width = im.width
            file.height = im.height
    except:
        pass

    # If the photo was uploaded, and not some other type of file,
    # then send to detection queue.
    if file.purpose == "photo":
        photo.queue_name = "detection"

    photo.updated_time = datetime.datetime.now()
    file.updated_time = datetime.datetime.now()

    await g.session.commit()

    result = photo_schema.dump(photo)

    if created:
        await current_app.dispatcher.dispatch_event("photos:created",
                "/photos/"+str(photo_id), current=result)
        return jsonify(result), HTTPStatus.CREATED
    else:
        await current_app.dispatcher.dispatch_event("photos:updated",
                "/photos/"+str(photo_id), current=result, previous=previous)
        return jsonify(result), HTTPStatus.OK
