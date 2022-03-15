import os

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_work_item_routes():
    """
    Test some work_item routes that should always work.
    """
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
async def test_work_item_with_upload():
    """
    Test a work item that requires an image upload.
    """
    async with app.test_client() as client:
        response = await client.post('/work-items', json={})
        assert response.status_code == 201 # Created
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['status'] == "created"

        item_url = '/work-items/{}'.format(data['id'])
        upload_url = 'work-items/{}/uploads/input.jpeg'.format(data['id'])

        response = await client.put(upload_url)
        assert response.status_code == 201 # Created
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['status'] == "ready"
        assert os.path.exists(data['filePath'])

        response = await client.delete(item_url)
        assert response.status_code == 200 # OK
        assert response.is_json
        data = await response.get_json()
        assert isinstance(data, dict)
        assert data['status'] == "ready"

        response = await client.delete(item_url)
        assert response.status_code == 404 # Not Found

        response = await client.get(item_url)
        assert response.status_code == 404 # Not Found


@pytest.mark.asyncio
async def test_work_item_crud():
    """
    Test some work_item routes that should always work.
    """

    new_item = {
        "fileUrl": "https://farm2.staticflickr.com/1100/3174128011_4fb033112d_z.jpg"
    }

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
