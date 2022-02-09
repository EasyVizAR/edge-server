import pytest


def test_import_app_object():
    """
    Make sure app object can be imported without error.
    """
    from server.main import app
    assert app is not None


@pytest.mark.asyncio
async def test_headsets_routes():
    """
    Test some headset routes that should always work.
    """
    from server.main import app
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
async def test_maps_routes():
    """
    Test some map routes that should always work.
    """
    from server.main import app
    async with app.test_client() as client:
        response = await client.get('/maps')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get('/maps/')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get('/maps?envelope=items')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data['items'], list)
