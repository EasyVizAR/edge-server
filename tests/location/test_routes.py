import os

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_location_routes():
    """
    Test location routes.
    """
    async with app.test_client() as client:
        # Initial list of locations
        response = await client.get("/locations")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        locations = await response.get_json()
        assert isinstance(locations, list)

        # Initial list of locations with envelope
        response = await client.get("/locations?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        locations2 = await response.get_json()
        assert isinstance(locations2, dict)
        assert isinstance(locations2['items'], list)

        # Create an object
        response = await client.post("/locations", json=dict(name="Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()
        assert isinstance(location, dict)
        assert location['id'] is not None
        assert location['name'] == "Test"

        location_url = "/locations/{}".format(location['id'])

        # Test getting the object back
        response = await client.get(location_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        location2 = await response.get_json()
        assert location2['id'] == location['id']
        assert location2['name'] == location['name']
        assert isinstance(location2['headset_configuration'], dict)

        qrcode_url = "/locations/{}/qrcode".format(location['id'])

        # Test getting the QR code
        response = await client.get(qrcode_url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers['Content-Type'].startswith("image/svg+xml")

        # Test changing the name
        response = await client.patch(location_url, json=dict(id="bad", name="Changed"))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        location2 = await response.get_json()
        assert location2['id'] == location['id']
        assert location2['name'] == "Changed"

        # Test replacement
        response = await client.put(location_url, json=location)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        location2 = await response.get_json()
        assert location2['id'] == location['id']
        assert location2['name'] == location['name']

        # Test deleting the object
        response = await client.delete(location_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        location2 = await response.get_json()
        assert location2['id'] == location['id']

        # Test creating object through PUT
        response = await client.put(location_url, json=location)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location2 = await response.get_json()
        assert location2['id'] == location['id']
        assert location2['name'] == location['name']

        # Test that object does not exist after DELETE
        response = await client.delete(location_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(location_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(location_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(location_url, json=dict(name="Changed"))
        assert response.status_code == HTTPStatus.NOT_FOUND
