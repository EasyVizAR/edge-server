import os

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_check_in_routes():
    """
    Test check-in routes.
    """
    async with app.test_client() as client:
        position = dict(x=0, y=0, z=0)

        response = await client.post("/headsets", json=dict(name="Test", position=position))
        assert response.status_code == 201
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)

        headers = {
            'Authorization': 'Bearer ' + headset['token']
        }

        headset_url = "/headsets/{}".format(headset['id'])
        check_ins_url = headset_url + "/check-ins"

        response = await client.get(check_ins_url)
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get(check_ins_url + "?envelope=items")
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data['items'], list)

        data = dict(location_id="place")

        response = await client.post(check_ins_url, headers=headers, json=data)
        assert response.status_code == 201
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)

        assert data['start_time'] > 0
        assert data['location_id'] == "place"

        # The location should have been updated in the headset object as well.
        response = await client.get(headset_url)
        assert response.status_code == 200
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(data, dict)
        assert headset2['location_id'] == "place"
        assert headset2['last_check_in_id'] == data['id']


@pytest.mark.asyncio
async def test_automatic_check_in():
    """
    Test automatic check-in creation.
    """
    async with app.test_client() as client:
        position = dict(x=0, y=0, z=0)

        response = await client.post("/headsets", json=dict(name="Test", location_id="location1"))
        assert response.status_code == 201
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['last_check_in_id'] is not None

        # Change position but not location
        headset_url = "/headsets/{}".format(headset['id'])
        response = await client.patch(headset_url, json={'position': position})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2['last_check_in_id'] == headset['last_check_in_id']

        # Change location - create a new check-in at that location
        response = await client.patch(headset_url, json={'location_id': "location2"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2['last_check_in_id'] != headset['last_check_in_id']

        checkin_url = "/headsets/{}/check-ins".format(headset['id'])
        response = await client.get(checkin_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        checkins = await response.get_json()
        assert isinstance(checkins, list)
        assert len(checkins) == 2
