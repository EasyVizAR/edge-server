import asyncio
import os

from http import HTTPStatus

from quart import Blueprint, current_app, request, make_response, jsonify, send_from_directory
from werkzeug import exceptions

from .models import WorkItem


work_items = Blueprint('work-items', __name__)


@work_items.route('/work-items', methods=['GET'])
async def list_work_items():
    """
    List work items
    ---
    get:
        description: >-
            List work items

            The optional filter parameters combined with a "wait" parameter
            make it possible for the caller to wait for notification of the
            next item.
        summary: List work items
        tags:
          - work-items
        parameters:
          - name: content-type
            in: query
            required: false
            description: Filter work items on content-type, e.g. "image/jpeg".
          - name: envelope
            in: query
            required: false
            description: If set, the returned list will be wrapped in an envelope with this name.
          - name: source-type
            in: query
            required: false
            description: Filter work items on source-type, e.g. "camera".
          - name: status
            in: query
            required: false
            description: Filter work items on status (created|ready|done).
          - name: wait
            in: query
            required: false
            description: >-
                Request that the server wait a time limit (in seconds) for a
                new result if none are immediately available. The server will
                return one or more results as soon as they are available, or if
                the time limit has passed, the server will return a No Content
                204 result indicating timeout. A time limit of 30-60 seconds is
                recommended.
        responses:
            200:
                description: A list of WorkItem objects
                content:
                    application/json:
                        schema:
                            type: array
                            items: WorkItem
    """

    # TODO: check authorization

    items = WorkItem.find(**request.args)

    # Wait for new objects if the query returned no results and the caller
    # specified a wait timeout. If there are still no results, we return a 204
    # No Content code.
    wait = float(request.args.get("wait", 0))
    if len(items) == 0 and wait > 0:
        try:
            item = await asyncio.wait_for(WorkItem.wait_for_work_item(**request.args), timeout=wait)
            items.append(item)
        except asyncio.TimeoutError:
            return jsonify([]), HTTPStatus.NO_CONTENT

    # Wrap the maps list if the caller requested an envelope.
    query = request.args
    if "envelope" in query:
        result = {query.get("envelope"): items}
    else:
        result = items

    return jsonify(result), HTTPStatus.OK


@work_items.route('/work-items', methods=['POST'])
async def create_work_item():
    """
    Create a WorkItem
    ---
    post:
        summary: Create a WorkItem
        description: >-
            Create a WorkItem

            A work item should include data for the worker to process, which is
            usually an image. The file may either be specified through a URL,
            which the worker can download to process, or it can be uploaded
            after creating the work item. If fileUrl is unspecified, then the
            server will set fileUrl to an appropriate upload UR, and the caller
            should upload the file using a PUT operation.
        tags:
          - work-items
        requestBody:
            required: true
            content:
                application/json:
                    schema: WorkItem
        responses:
            201:
                description: The created WorkItem object
                content:
                    application/json:
                        schema: WorkItem
    """
    # TODO: Require authentication

    body = await request.get_json()

    new_id = WorkItem.get_next_id()
    new_item = WorkItem(new_id, **body)

    # The work item either needs to specify a fileUrl for the worker to
    # process, or the caller will need to upload a file before the work item is
    # ready to be processed.
    if new_item.fileUrl is None:
        if new_item.contentType == "image/jpeg":
            extension = "jpeg"
        elif new_item.contentType == "image/png":
            extension = "png"
        else:
            error = "Unsupported content type ({})".format(new_item.contentType)
            raise exceptions.BadRequest(description=error)

        upload_file_name = "{}.{}".format(new_item.file_basename(), extension)
        new_item.filePath = os.path.join(WorkItem.base_dir(), "data", upload_file_name)

        # Inform the caller where to upload the file.
        new_item.fileUrl = "/work-items/data/{}".format(upload_file_name)

    else:
        new_item.status = "ready"

    new_item.save()

    return jsonify(new_item), HTTPStatus.CREATED


@work_items.route('/work-items/<work_item_id>', methods=['GET'])
async def get_work_item(work_item_id):
    """
    Get a WorkItem by ID
    ---
    get:
        summary: Get a WorkItem by ID
        tags:
          - work-items
        responses:
            200:
                description: A WorkItem object
                content:
                    application/json:
                        schema: WorkItem
    """
    item = WorkItem.find_by_id(work_item_id)

    if item is None:
        raise exceptions.NotFound(description="Work item was not found")

    return jsonify(item), HTTPStatus.OK


@work_items.route('/work-items/data/<filename>', methods=['GET'])
async def get_work_item_file(filename):
    """
    Get a WorkItem data file
    ---
    get:
        summary: Get a WorkItem data file
        description: >-
            Use this method to fetch a data file such as an image associated
            with a work item. This method will only succeed if the the data
            file is stored on the same host (fileUrl is a relative path in the
            work item) and the work item status is "ready" or "done".
        tags:
          - work-items
        responses:
            200:
                description: The image or other data file.
                content:
                    image/jpeg: {}
                    image/png: {}
    """
    data_dir = os.path.join(WorkItem.base_dir(), "data")
    return await send_from_directory(data_dir, filename)


@work_items.route('/work-items/data/<filename>', methods=['PUT'])
async def upload_work_item_file(filename):
    """
    Replace a WorkItem data file
    ---
    post:
        summary: Replace a WorkItem data file
        description: >-
            Use this method to upload a data file such as an image to accompany
            a work item. This should be used after creating a work item with an
            empty fileUrl, in which case, after which the server will have
            determined the work item ID and path for the data file.
        tags:
          - work-items
        requestBody:
            required: true
            content:
                image/jpeg: {}
                image/png: {}
        responses:
            200:
                description: The updated WorkItem object
                content:
                    application/json:
                        schema: WorkItem
    """
    # TODO: Require authentication

    data_dir = os.path.join(WorkItem.base_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)

    work_item = None
    for item in WorkItem.find():
        if item.fileUrl == "/work-items/data/{}".format(filename):
            work_item = item
            break

    if work_item is None:
        raise exceptions.NotFound(description="No open work item found for file upload")

    body = await request.get_data()
    with open(work_item.filePath, "wb") as output:
        output.write(body)

    work_item.status = "ready"
    work_item.save()

    return jsonify(work_item), HTTPStatus.CREATED
