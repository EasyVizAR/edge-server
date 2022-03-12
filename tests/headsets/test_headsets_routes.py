import pytest

from server.main import app


@pytest.mark.asyncio
async def test_headsets_routes():
    """
    Test some headset routes that should always work.
    """
    async with app.test_client() as client:
        response = await client.get('/headsets')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get('/headsets/')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        position = dict(x=0, y=0, z=0)
        response = await client.post("/headsets", json=dict(name="test", position=position))
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)

        response = await client.get('/headsets?envelope=items')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data['items'], list)


@pytest.mark.asyncio
async def test_headset_updates():
    """
    Test updating headset name and pose.
    """
    async with app.test_client() as client:
        position = dict(x=0, y=0, z=0)
        response = await client.post("/headsets", json=dict(name="test", position=position))
        assert response.status_code == 200
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)

        headset_url = "/headsets/{}".format(headset['id'])
        response = await client.put(headset_url, json=dict(name="test2"))
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['name'] == "test2"
        for k in position.keys():
            assert data['position'][k] == position[k]

        position['x'] = 10

        response = await client.put(headset_url, json=dict(name="test3", position=position))
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['name'] == "test3"
        for k in position.keys():
            assert data['position'][k] == position[k]

        position['y'] = 20
        orientation = dict(x=0, y=0, z=1)

        response = await client.put(headset_url, json=dict(name="test4", position=position, orientation=orientation))
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['name'] == "test4"
        for k in position.keys():
            assert data['position'][k] == position[k]
            assert data['orientation'][k] == orientation[k]

        response = await client.get(headset_url + "/poses")
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 3
        for k in position.keys():
            assert int(data[-1]['position'][k]) == position[k]
            assert int(data[-1]['orientation'][k]) == orientation[k]

        response = await client.delete(headset_url)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_headset_pose_crud():
    """
    Test CRUD operations on headset poses.
    """
    async with app.test_client() as client:
        position = dict(x=0, y=0, z=0)
        response = await client.post("/headsets", json=dict(name="test", position=position))
        assert response.status_code == 200
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)

        poses_url = "/headsets/{}/poses".format(headset['id'])

        position = dict(x=1, y=0, z=0)
        orientation = dict(x=1, y=0, z=0)
        response = await client.post(poses_url, json=dict(position=position, orientation=orientation))
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        for k in position.keys():
            assert data['position'][k] == position[k]
            assert data['orientation'][k] == orientation[k]

        response = await client.get(poses_url)
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for k in position.keys():
            assert int(data[-1]['position'][k]) == position[k]
            assert int(data[-1]['orientation'][k]) == orientation[k]

        response = await client.get(poses_url + "?envelope=items")
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert isinstance(data['items'], list)
        assert len(data['items']) >= 1

        response = await client.delete("/headsets/{}".format(headset['id']))
        assert response.status_code == 200
