import os

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_pose_change_routes():
    """
    Test pose change routes.
    """
    async with app.test_client() as client:
        position = dict(x=0, y=0, z=0)

        response = await client.post("/headsets", json=dict(name="Test", position=position))
        assert response.status_code == 201
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)

        headset_url = "/headsets/{}".format(headset['id'])
        pose_changes_url = headset_url + "/pose-changes"

        response = await client.get(pose_changes_url)
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get(pose_changes_url + "/")
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get(pose_changes_url + "?envelope=items")
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data['items'], list)

        data = dict(position=dict(x=1, y=2, z=3))

        response = await client.post(pose_changes_url, json=data)
        assert response.status_code == 201
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)

        assert data['time'] > 0
        assert int(data['position']['x']) == 1
        assert int(data['position']['y']) == 2
        assert int(data['position']['z']) == 3
        assert int(data['orientation']['x']) == 0
        assert int(data['orientation']['y']) == 0
        assert int(data['orientation']['z']) == 0

        # The position should have been updated in the headset object as well.
        response = await client.get(headset_url)
        assert response.status_code == 200
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(data, dict)
        assert int(headset2['position']['x']) == 1
        assert int(headset2['position']['y']) == 2
        assert int(headset2['position']['z']) == 3
