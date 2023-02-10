import os

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_scene_routes():
    """
    Test scene routes
    """
    # Name of a field within the resource which we can change and test.
    test_field = "uploadedBy"
    test_value = "aoeu"

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Scene Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        scenes_url = "/locations/{}/scenes".format(location['id'])
        test_url = "/locations/{}/scenes/0000/scene.json".format(location['id'])

        # Test creating a scene with a dummy headset ID
        response = await client.put(test_url, json={test_field: test_value})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        scene = await response.get_json()
        assert scene['headset_id'] == "0000"

        # Test getting the new scene file
        response = await client.get(test_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert data[test_field] == test_value

        # The URL returned in the scene descriptor should also be valid
        response = await client.get(scene['file_url'])
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert data[test_field] == test_value

        # Test replacement
        test_value = "12345"
        response = await client.put(test_url, json={test_field: test_value})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        scene2 = await response.get_json()
        assert scene2['headset_id'] == "0000"
        assert scene2['modified'] > scene['modified']

        # Should return the new data
        response = await client.get(scene['file_url'])
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert data[test_field] == test_value

        # Scene should appear in the list
        response = await client.get(scenes_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert len(data) == 1
        assert data[0]['headset_id'] == "0000"
        assert data[0]['modified'] == scene2['modified']

        # Try list with envelope
        response = await client.get(scenes_url + "?envelope=wrapped")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert len(data['wrapped']) == 1
        assert data['wrapped'][0]['headset_id'] == "0000"
        assert data['wrapped'][0]['modified'] == scene2['modified']
