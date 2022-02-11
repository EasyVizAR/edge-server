import asyncio

from http import HTTPStatus

from quart import Blueprint, current_app, request, make_response, jsonify

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

    items = WorkItem.get_all(**request.args)

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
        description: Create a WorkItem
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
    new_item.save()

    # TODO: Set Location header if file upload is expected.

    return jsonify(new_item), HTTPStatus.CREATED
