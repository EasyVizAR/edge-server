import os

from http import HTTPStatus

import pytest

from server.main import app
from server.utils.testing import int_equal


@pytest.mark.asyncio
async def test_layer_routes():
    """
    Test layer routes
    """
    # Name of a field within the resource which we can change and test.
    test_field = "name"

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        layers_url = "/locations/{}/layers".format(location['id'])

        # Initial list of layers
        response = await client.get(layers_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layers = await response.get_json()
        assert isinstance(layers, list)

        # Initial list of layers with envelope
        response = await client.get(layers_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layers2 = await response.get_json()
        assert isinstance(layers2, dict)
        assert isinstance(layers2['items'], list)

        # Create an object
        response = await client.post(layers_url, json={test_field: "foo"})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        layer = await response.get_json()
        assert isinstance(layer, dict)
        assert layer['id'] is not None
        assert layer[test_field] == "foo"

        layer_url = "{}/{}".format(layers_url, layer['id'])

        # Test getting the object back
        response = await client.get(layer_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layer2 = await response.get_json()
        assert int_equal(layer2['id'], layer['id'])
        assert layer2[test_field] == layer[test_field]

        # Test changing the name
        response = await client.patch(layer_url, json={"id": "bad", test_field: "bar"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layer2 = await response.get_json()
        assert int_equal(layer2['id'], layer['id'])
        assert layer2[test_field] == "bar"

        # Test replacement
        response = await client.put(layer_url, json=layer)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layer2 = await response.get_json()
        assert int_equal(layer2['id'], layer['id'])
        assert layer2[test_field] == layer[test_field]

        # Test deleting the object
        response = await client.delete(layer_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layer2 = await response.get_json()
        assert int_equal(layer2['id'], layer['id'])

        # Test creating object through PUT
        response = await client.put(layer_url, json=layer)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        layer2 = await response.get_json()
        assert int_equal(layer2['id'], layer['id'])
        assert layer2[test_field] == layer[test_field]

        # Test that object does not exist after DELETE
        response = await client.delete(layer_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(layer_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(layer_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(layer_url, json={test_field: "bar"})
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_layer_upload():
    """
    Test layer upload
    """
    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        layers_url = "/locations/{}/layers".format(location['id'])

        # Create an object
        response = await client.post(layers_url, json={"type": "uploaded"})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        layer = await response.get_json()
        assert isinstance(layer, dict)
        assert layer['id'] is not None
        assert layer['type'] == "uploaded"

        layer_url = "{}/{}".format(layers_url, layer['id'])

        # Test upload process
        response = await client.put(layer['imageUrl'], data="test")
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        layer2 = await response.get_json()
        assert isinstance(layer, dict)
        assert int_equal(layer2['id'], layer['id'])
        assert layer2['updated'] > layer['updated']

        # Test downloading the file
        response = await client.get(layer['imageUrl'])
        assert response.status_code == HTTPStatus.OK
        data = await response.get_data()
        assert data == "test".encode('utf-8')

        # Test deleting the object
        response = await client.delete(layer_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        layer2 = await response.get_json()
        assert int_equal(layer2['id'], layer['id'])
