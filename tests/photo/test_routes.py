import os

from http import HTTPStatus

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
        response = await client.post(photos_url, json=dict(imageUrl="/foo"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['id'] is not None
        assert photo['imageUrl'] == "/foo"

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
        response = await client.post(photos_url, json=dict(contentType="image/jpeg"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['ready'] is False

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
        response = await client.post(photos_url, json=dict(contentType="image/jpeg"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['ready'] is False
        assert isinstance(photo['annotations'], list)
        assert len(photo['annotations']) == 0

        photo_url = "/photos/{}".format(photo['id'])

        # Annotate the image
        update = {
            "width": 640,
            "height": 480,
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
        assert isinstance(photo2['annotations'], list)
        assert len(photo2['annotations']) == 1
        assert photo2['annotations'][0]['label'] == "extinguisher"
