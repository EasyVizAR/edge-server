import os
import time

from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_photo_routes():
    """
    Test photo routes
    """
    async with app.test_client() as client:
        photos_url = "/photos"

        # Initial list of photos
        response = await client.get(photos_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photos = await response.get_json()
        assert isinstance(photos, list)

        # Initial list of photos with envelope
        response = await client.get(photos_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photos2 = await response.get_json()
        assert isinstance(photos2, dict)
        assert isinstance(photos2['items'], list)

        # Create an object
        photo_data = {
            "imageUrl": "/foo",
            "retention": "temporary"
        }
        response = await client.post(photos_url, json=photo_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['id'] is not None
        assert photo['imageUrl'] == "/foo"
        assert photo['retention'] != "auto"

        photo_url = "{}/{}".format(photos_url, photo['id'])

        # Test getting the object back
        response = await client.get(photo_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['imageUrl'] == photo['imageUrl']

        # Test changing the name
        response = await client.patch(photo_url, json=dict(id="bad", imageUrl="/bar"))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['imageUrl'] == "/bar"

        # Test replacement
        response = await client.put(photo_url, json=photo)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['imageUrl'] == photo['imageUrl']

        # Test deleting the object
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']

        # Test creating object through PUT
        response = await client.put(photo_url, json=photo)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['imageUrl'] == photo['imageUrl']

        # Test that object does not exist after DELETE
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(photo_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(photo_url, json=dict(imageUrl="/bar"))
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_photo_upload():
    """
    Test photo upload
    """
    async with app.test_client() as client:
        photos_url = "/photos"

        # Create an object
        photo_data = {
            "contentType": "image/jpeg",
            "retention": "temporary"
        }
        response = await client.post(photos_url, json=photo_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['ready'] is False
        assert photo['status'] == "created"
        assert photo['retention'] != "auto"

        photo_url = "/photos/{}".format(photo['id'])

        # Test upload process
        response = await client.put(photo['imageUrl'], data="test")
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo2 = await response.get_json()
        assert isinstance(photo, dict)
        assert photo2['id'] == photo['id']
        assert photo2['ready'] is True
        assert photo2['updated'] > photo['updated']
        assert photo2['status'] == "ready"

        # Test downloading the file
        response = await client.get(photo['imageUrl'])
        assert response.status_code == HTTPStatus.OK
        data = await response.get_data()
        assert data == "test".encode('utf-8')

        # Test deleting the object
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']


@pytest.mark.asyncio
async def test_photo_annotations():
    """
    Test photo annotations
    """
    async with app.test_client() as client:
        photos_url = "/photos"

        # Create an object
        photo_data = {
            "contentType": "image/jpeg",
            "retention": "temporary"
        }
        response = await client.post(photos_url, json=photo_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['ready'] is False
        assert isinstance(photo['annotations'], list)
        assert len(photo['annotations']) == 0
        assert photo['status'] == "created"
        assert photo['retention'] != "auto"

        photo_url = "/photos/{}".format(photo['id'])

        # Annotate the image
        update = {
            "width": 640,
            "height": 480,
            "status": "done",
            "annotations": [{
                "label": "extinguisher",
                "boundary": {
                    "left": 0.1,
                    "top": 0.1,
                    "width": 0.5,
                    "height": 0.5
                }
            }]
        }
        response = await client.patch(photo_url, json=update)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['width'] == 640
        assert photo2['height'] == 480
        assert photo2['status'] == "done"
        assert isinstance(photo2['annotations'], list)
        assert len(photo2['annotations']) == 1
        assert photo2['annotations'][0]['label'] == "extinguisher"

        # Clean up
        await client.delete(photo_url)


@pytest.mark.asyncio
async def test_photo_long_polling():
    """
    Test photo long polling
    """
    async with app.test_client() as client:
        photos_url = "/photos"
        start_time = time.time()

        # Initial list of photos should be empty
        response = await client.get(photos_url + "?since={}".format(start_time))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photos = await response.get_json()
        assert isinstance(photos, list)
        assert len(photos) == 0

        # A short wait should timeout with no results
        response = await client.get(photos_url + "?since={}&wait=0.001".format(start_time))
        assert response.status_code == HTTPStatus.NO_CONTENT
        assert response.is_json
        photos = await response.get_json()
        assert isinstance(photos, list)
        assert len(photos) == 0

        # Set up a listener
        listener = client.get(photos_url + "?since={}&wait=5".format(start_time))

        # Create an object
        response = await client.post(photos_url, json=dict(imageUrl="/foo"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['id'] is not None
        assert photo['imageUrl'] == "/foo"

        # The listener should have received the same object
        response2 = await listener
        assert response2.status_code == HTTPStatus.OK
        assert response2.is_json
        photo2 = await response2.get_json()
        assert isinstance(photo2, list)
        assert photo2[0] == photo


@pytest.mark.asyncio
async def test_photo_empty_url():
    """
    Test creating photo with an empty URL string
    """
    async with app.test_client() as client:
        photos_url = "/photos"

        # Create an object
        data = {
            "contentType": "image/png",
            "imageUrl": "    "
        }

        response = await client.post(photos_url, json=data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['ready'] is False
        assert photo['imageUrl'].startswith('/photos')
        assert photo['imagePath'].endswith('.png')


@pytest.mark.asyncio
async def test_photo_status_change_long_polling():
    """
    Test photo status change long polling
    """
    async with app.test_client() as client:
        photos_url = "/photos"
        start_time = time.time()

        # Create an object
        photo_data = {
            "imageUrl": "/foo",
            "retention": "temporary"
        }
        response = await client.post(photos_url, json=photo_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['id'] is not None
        assert photo['imageUrl'] == "/foo"
        assert photo['status'] == "ready"
        assert photo['retention'] != "auto"

        # Set up a listener
        photo_url = "/photos/{}".format(photo['id'])
        listener = client.get(photo_url + "?status=done&wait=5")

        # Change the photo status
        response2 = await client.patch(photo_url, json=dict(status="done"))
        assert response2.status_code == HTTPStatus.OK
        assert response2.is_json
        photo2 = await response2.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['status'] == "done"

        # The listener should have received the same object
        response3 = await listener
        assert response3.status_code == HTTPStatus.OK
        assert response3.is_json
        photo3 = await response3.get_json()
        assert photo3['id'] == photo['id']
        assert photo3['status'] == "done"

        # Clean up
        await client.delete(photo_url)


@patch('server.photo.routes.Image')
def test_process_uploaded_photo_file(Image):
    from server.photo.routes import process_uploaded_photo_file

    photo = MagicMock()
    photo.files = []

    image = MagicMock()
    image.width = 640
    image.height = 480
    image.format = "PNG"
    Image.open.return_value.__enter__.return_value = image

    process_uploaded_photo_file(photo, "test.png", "test.png", "photo")

    # The function should modify these attributes based on the fake uploaded file.
    # It should add a photo entry and a thumbnail entry to the file list.
    assert photo.width == image.width
    assert photo.height == image.height
    assert len(photo.files) == 2

    # Repeating the request should not add any new files, but replace the existing.
    process_uploaded_photo_file(photo, "test.png", "test.png", "photo")
    assert photo.width == image.width
    assert photo.height == image.height
    assert len(photo.files) == 2

    image.width = 333
    image.height = 333

    process_uploaded_photo_file(photo, "other.png", "other.png", "test")

    # This should not change the attributes in the photo object because it is
    # not a primary photo, but it should still append to the file list.
    assert photo.width != image.width
    assert photo.height != image.height
    assert len(photo.files) == 3
