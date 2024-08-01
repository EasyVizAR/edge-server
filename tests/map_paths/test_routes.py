import os

from http import HTTPStatus

import pytest

from server.main import app
from server.utils.testing import int_equal


@pytest.mark.asyncio
async def test_map_path_routes():
    """
    Test map path routes
    """

    example_object = {
        "label": "foo",
        "type": "navigation",
        "points": [[0, 0, 0], [1, 0, 0], [1, 0, 1]]
    }

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Map Path Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        resource_url = "/locations/{}/map-paths".format(location['id'])

        # Initial list should be empty
        response = await client.get(resource_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        items = await response.get_json()
        assert isinstance(items, list)

        # Initial list with envelope
        response = await client.get(resource_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        wrapped = await response.get_json()
        assert isinstance(wrapped, dict)
        assert isinstance(wrapped['items'], list)

        # Create an object
        response = await client.post(resource_url, json=example_object)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        item = await response.get_json()
        assert isinstance(item, dict)
        assert item['id'] is not None

        item_url = "{}/{}".format(resource_url, item['id'])

        # Test getting the object back
        response = await client.get(item_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        item2 = await response.get_json()
        assert int_equal(item2['id'], item['id'])

        # Test filter with a mobile device ID.  This should still return the
        # item because we allow null values to match any specific query.
        response = await client.get(resource_url + "?mobile_device_id=e94f721d-e7e0-40bc-a29e-48b59b425fa1")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        items2 = await response.get_json()
        assert isinstance(items2, list)
        assert items2[0]['id'] == item['id']

        # Test changing the name
        response = await client.patch(item_url, json={"label": "bar"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        item2 = await response.get_json()
        assert int_equal(item2['id'], item['id'])
        assert item2['label'] == "bar"

        # Test replacement
        response = await client.put(resource_url + "?type=navigation", json=example_object)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        item2 = await response.get_json()
        assert int_equal(item2['id'], item['id'])
        assert item2['label'] == item['label']

        # Test deleting the object
        response = await client.delete(item_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        item2 = await response.get_json()
        assert int_equal(item2['id'], item['id'])

        # Test creating object through PUT
        response = await client.put(resource_url + "?type=navigation", json=example_object)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        item2 = await response.get_json()
        assert item2['label'] == item['label']

        # The ID may have changed after the upsert operation
        item_url = "{}/{}".format(resource_url, item2['id'])

        # Test that object does not exist after DELETE
        response = await client.delete(item_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(item_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(item_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(item_url, json={"label": "bar"})
        assert response.status_code == HTTPStatus.NOT_FOUND

        # Clean up
        response = await client.delete('/locations/{}'.format(location['id']))
        assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_map_path_unity_fixes():
    """
    Test map path unity fixes
    """
    example_object = {
        "label": "bar",
        "type": "navigation",
        "points": [
            {"x": 0, "y": 0, "z": 0},
            {"x": 1, "y": 0, "z": 0},
            {"x": 1, "y": 0, "z": 1},
        ]
    }

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Map Path Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        resource_url = "/locations/{}/map-paths".format(location['id'])

        # Initial list should be empty
        response = await client.get(resource_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        items = await response.get_json()
        assert isinstance(items, list)

        # Create an object
        response = await client.post(resource_url, json=example_object)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        item = await response.get_json()
        assert isinstance(item, dict)
        assert item['id'] is not None
        assert len(item['points']) == 3

        item_url = "{}/{}".format(resource_url, item['id'])

        # Test with inflate vectors option
        response = await client.get(resource_url + "?inflate_vectors=T")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        items = await response.get_json()
        assert isinstance(items, list)
        assert items[0]['id'] is not None
        assert len(items[0]['points']) == 3
        for i, point in enumerate(items[0]['points']):
            assert isinstance(point, dict)
            assert int(point['x']) == int(example_object['points'][i]['x'])

        # Test that object does not exist after DELETE
        response = await client.delete(item_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(item_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(item_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(item_url, json={"label": "bar"})
        assert response.status_code == HTTPStatus.NOT_FOUND

        # Clean up
        response = await client.delete('/locations/{}'.format(location['id']))
        assert response.status_code == HTTPStatus.OK
