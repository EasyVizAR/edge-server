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
        response = await client.post(photos_url, json=dict(fileUrl="/foo"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()
        assert isinstance(photo, dict)
        assert photo['id'] is not None
        assert photo['fileUrl'] == "/foo"

        photo_url = "{}/{}".format(photos_url, photo['id'])

        # Test getting the object back
        response = await client.get(photo_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['fileUrl'] == photo['fileUrl']

        # Test changing the name
        response = await client.patch(photo_url, json=dict(id="bad", fileUrl="/bar"))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['fileUrl'] == "/bar"

        # Test replacement
        response = await client.put(photo_url, json=photo)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
        assert photo2['fileUrl'] == photo['fileUrl']

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
        assert photo2['fileUrl'] == photo['fileUrl']

        # Test that object does not exist after DELETE
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(photo_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(photo_url, json=dict(fileUrl="/bar"))
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
        assert photo['status'] == "created"

        photo_url = "/photos/{}".format(photo['id'])

        # Test upload process
        response = await client.put(photo['fileUrl'], data="test")
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo2 = await response.get_json()
        assert isinstance(photo, dict)
        assert photo2['id'] == photo['id']
        assert photo2['status'] == "ready"
        assert photo2['updated'] > photo['updated']

        # Test downloading the file
        response = await client.get(photo['fileUrl'])
        assert response.status_code == HTTPStatus.OK
        data = await response.get_data()
        assert data == "test".encode('utf-8')

        # Test deleting the object
        response = await client.delete(photo_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        photo2 = await response.get_json()
        assert photo2['id'] == photo['id']
