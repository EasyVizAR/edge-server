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
        test_url = "{}/0000.json".format(scenes_url)

        # Test creating a scene with a dummy headset ID
        response = await client.put(test_url, json={test_field: test_value})
        assert response.status_code == HTTPStatus.NO_CONTENT

        # Test getting the new scene file
        response = await client.get(test_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert data[test_field] == test_value

        # Scene should appear in the list
        response = await client.get(scenes_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert len(data) > 0
        assert "0000" in data

        # Try list with envelope
        response = await client.get(scenes_url + "?envelope=wrapped")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        data = await response.get_json()
        assert len(data['wrapped']) > 0
        assert "0000" in data['wrapped']
