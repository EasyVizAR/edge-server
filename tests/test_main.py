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


@pytest.mark.asyncio
async def test_work_item_routes():
    """
    Test some work_item routes that should always work.
    """
    from server.main import app
    async with app.test_client() as client:
        response = await client.get('/work-items')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get('/work-items/')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, list)

        response = await client.get('/work-items?envelope=items')
        assert response.status_code == 200
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data['items'], list)


@pytest.mark.asyncio
async def test_work_item_crud():
    """
    Test some work_item routes that should always work.
    """

    new_item = {
        "fileUrl": "https://farm2.staticflickr.com/1100/3174128011_4fb033112d_z.jpg"
    }

    from server.main import app
    async with app.test_client() as client:
        response = await client.post('/work-items', json=new_item)
        assert response.status_code == 201 # Created
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['fileUrl'] == new_item['fileUrl']
        assert data['status'] == "ready"

        # Save the created work-item ID for future tests
        new_item['id'] = data['id']
        item_url = '/work-items/{}'.format(new_item['id'])

        response = await client.get(item_url)
        assert response.status_code == 200 # OK
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['fileUrl'] == new_item['fileUrl']
        assert data['status'] == "ready"

        # Make a valid change to the item and update it
        data['status'] = "done"

        response = await client.put(item_url, json=data)
        assert response.status_code == 200 # OK
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['fileUrl'] == new_item['fileUrl']
        assert data['status'] == "done"

        # Make a disallowed change to the item and update it
        data['id'] = new_item['id'] + 1

        response = await client.put(item_url, json=data)
        assert response.status_code == 400 # Bad Request

        response = await client.delete(item_url)
        assert response.status_code == 200 # OK
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['fileUrl'] == new_item['fileUrl']
        assert data['status'] == "done"

        response = await client.delete(item_url)
        assert response.status_code == 404 # Not Found

        response = await client.get(item_url)
        assert response.status_code == 404 # Not Found
