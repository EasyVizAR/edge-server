import os
import uuid

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_pose_change_routes():
    """
    Test pose change routes.
    """
    test_location_id = str(uuid.uuid4())

    async with app.test_client() as client:
        position = dict(x=2, y=5, z=7)
        orientation = dict(x=0, y=0, z=0, w=1)

        response = await client.post("/headsets", json=dict(name="Test", position=position, orientation=orientation, location_id=test_location_id))
        assert response.status_code == 201
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['name'] == 'Test'

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

        data = dict(position=dict(x=1, y=2, z=3), orientation=dict(x=0, y=0, z=0, w=1))

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

        other_url = "/headsets/{}/check-ins/{}/pose-changes".format(headset['id'], headset['last_check_in_id'])
        response = await client.get(other_url)
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Cleanup
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.OK
