import os
import uuid

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_surface_routes():
    """
    Test surface routes
    """
    # Name of a field within the resource which we can change and test.
    test_field = "uploadedBy"

    test_surface_id = str(uuid.uuid4())

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Surface Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        surfaces_url = "/locations/{}/surfaces".format(location['id'])

        # Initial list of surfaces
        response = await client.get(surfaces_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surfaces = await response.get_json()
        assert isinstance(surfaces, list)

        # Initial list of surfaces with envelope
        response = await client.get(surfaces_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surfaces2 = await response.get_json()
        assert isinstance(surfaces2, dict)
        assert isinstance(surfaces2['items'], list)

        # Create an object
        surface_url = "/locations/{}/surfaces/{}".format(location['id'], test_surface_id)
        response = await client.put(surface_url, json={})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        surface = await response.get_json()
        assert isinstance(surface, dict)
        assert surface['id'] == test_surface_id

        # Test getting the object back
        response = await client.get(surface_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert surface2['id'] == surface['id']

        # Test replacement
        response = await client.put(surface_url, json=surface)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert surface2['id'] == surface['id']

        # Test deleting the object
        response = await client.delete(surface_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert surface2['id'] == surface['id']

        # Test creating object through PUT
        response = await client.put(surface_url, json=surface)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        surface2 = await response.get_json()
        assert surface2['id'] == surface['id']

        # Test that object does not exist after DELETE
        response = await client.delete(surface_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(surface_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(surface_url)
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_surface_upload():
    """
    Test surface upload
    """
    test_surface_id = str(uuid.uuid4())

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Surface Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        surfaces_url = "/locations/{}/surfaces".format(location['id'])

        # Create an object
        surface_url = "{}/{}".format(surfaces_url, test_surface_id)
        response = await client.put(surface_url, json={})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        surface = await response.get_json()
        assert isinstance(surface, dict)
        assert surface['id'] == test_surface_id

        # Test upload process
        response = await client.put(surface['fileUrl'], data="ply")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert isinstance(surface, dict)
        assert surface2['id'] == surface['id']
        assert surface2['updated'] > surface['updated']

        # Test downloading the file
        response = await client.get(surface['fileUrl'])
        assert response.status_code == HTTPStatus.OK
        data = await response.get_data()
        assert data == "ply".encode('utf-8')

        # Test deleting the object
        response = await client.delete(surface_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert surface2['id'] == surface['id']


@pytest.mark.asyncio
async def test_direct_surface_upload():
    """
    Test direct surface upload
    """
    test_surface_id = str(uuid.uuid4())

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Surface Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        surface_ply_url = "/locations/{}/surfaces/{}/surface.ply".format(location['id'], test_surface_id)

        # Test upload process
        response = await client.put(surface_ply_url, data="ply")
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        surface = await response.get_json()
        assert isinstance(surface, dict)
        assert surface['id'] == test_surface_id

        # Test downloading the file
        response = await client.get(surface_ply_url)
        assert response.status_code == HTTPStatus.OK
        data = await response.get_data()
        assert data == "ply".encode('utf-8')

        surface_url = "/locations/{}/surfaces/{}".format(location['id'], surface['id'])

        # Test deleting the object
        response = await client.delete(surface_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert surface2['id'] == surface['id']


@pytest.mark.asyncio
async def test_clear_surfaces():
    """
    Test clear surfaces
    """
    test_surface_id = str(uuid.uuid4())

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Surface Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        surfaces_url = "/locations/{}/surfaces".format(location['id'])

        # Create an object
        surface_url = "/locations/{}/surfaces/{}".format(location['id'], test_surface_id)
        response = await client.put(surface_url, json={})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        surface = await response.get_json()
        assert isinstance(surface, dict)
        assert surface['id'] == test_surface_id

        # Test upload process
        response = await client.put(surface['fileUrl'], data="ply")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surface2 = await response.get_json()
        assert isinstance(surface, dict)
        assert surface2['id'] == surface['id']
        assert surface2['updated'] > surface['updated']

        # Test deleting all surfaces
        response = await client.delete(surfaces_url)
        assert response.status_code == HTTPStatus.OK

        # List of surfaces should be empty now
        response = await client.get(surfaces_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        surfaces = await response.get_json()
        assert isinstance(surfaces, list)
        assert len(surfaces) == 0
