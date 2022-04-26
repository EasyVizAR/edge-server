import os

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_headset_routes():
    """
    Test headset routes
    """
    # Name of a field within the resource which we can change and test.
    test_field = "name"

    async with app.test_client() as client:
        headsets_url = "/headsets"

        # Initial list of headsets
        response = await client.get(headsets_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headsets = await response.get_json()
        assert isinstance(headsets, list)

        # Initial list of headsets with envelope
        response = await client.get(headsets_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headsets2 = await response.get_json()
        assert isinstance(headsets2, dict)
        assert isinstance(headsets2['items'], list)

        # Create an object
        response = await client.post(headsets_url, json={test_field: "foo"})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['id'] is not None
        assert headset[test_field] == "foo"

        headset_url = "{}/{}".format(headsets_url, headset['id'])

        # Test getting the object back
        response = await client.get(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2[test_field] == headset[test_field]

        # Test changing the name
        response = await client.patch(headset_url, json={"id": "bad", test_field: "bar"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2[test_field] == "bar"

        # Test replacement
        response = await client.put(headset_url, json=headset)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2[test_field] == headset[test_field]

        # Test deleting the object
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']

        # Test creating object through PUT
        response = await client.put(headset_url, json=headset)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2[test_field] == headset[test_field]

        # Test that object does not exist after DELETE
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(headset_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(headset_url, json={test_field: "bar"})
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_headset_put_updates():
    """
    Test headset PUT updates
    """
    async with app.test_client() as client:
        headsets_url = "/headsets"

        # Create an object
        response = await client.post(headsets_url, json=dict(name="Test PUT"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['id'] is not None
        assert headset['name'] == "Test PUT"
        assert headset['position'] is not None
        assert headset['orientation'] is not None

        headset_url = "{}/{}".format(headsets_url, headset['id'])

        # Test changing position only
        updated = headset.copy()
        updated['position'] = dict(x=1, y=1, z=1)
        response = await client.put(headset_url, json=updated)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == updated['position']
        assert headset2['orientation'] == updated['orientation']
        assert headset2['updated'] > updated['updated']

        # Test changing orientation only
        updated = headset2.copy()
        updated['orientation'] = dict(x=1, y=0, z=0, w=0)
        response = await client.put(headset_url, json=updated)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == updated['position']
        assert headset2['orientation'] == updated['orientation']
        assert headset2['updated'] > updated['updated']

        # Test changing position and orientation
        updated = headset2.copy()
        updated['position'] = dict(x=2, y=2, z=2)
        updated['orientation'] = dict(x=1, y=0, z=0, w=0)
        response = await client.put(headset_url, json=updated)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == updated['position']
        assert headset2['orientation'] == updated['orientation']
        assert headset2['updated'] > updated['updated']

        # Test GET headset returns an appropriate object
        response = await client.get(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2['position'] == updated['position']
        assert headset2['orientation'] == updated['orientation']
        assert headset2['updated'] > headset['updated']

        # Test pose changes returns all of the changes
        pose_changes_url = "/headsets/{}/pose-changes".format(headset['id'])
        response = await client.get(pose_changes_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        changes = await response.get_json()
        assert isinstance(changes, list)
        assert len(changes) == 3
        assert int(changes[0]['position']['x']) == 1
        assert int(changes[1]['orientation']['x']) == 1
        assert int(changes[2]['position']['x']) == 2

        # Test deleting the object
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']


@pytest.mark.asyncio
async def test_headset_patch_updates():
    """
    Test headset PATCH updates
    """
    async with app.test_client() as client:
        headsets_url = "/headsets"

        # Create an object
        response = await client.post(headsets_url, json=dict(name="Test PATCH"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['id'] is not None
        assert headset['name'] == "Test PATCH"
        assert headset['position'] is not None
        assert headset['orientation'] is not None

        headset_url = "{}/{}".format(headsets_url, headset['id'])

        # Test changing position only
        position = dict(x=1, y=1, z=1)
        response = await client.patch(headset_url, json=dict(position=position))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == position
        assert headset2['orientation'] == headset['orientation']
        assert headset2['updated'] > headset['updated']

        # Test changing orientation only
        orientation = dict(x=1, y=0, z=0, w=0)
        response = await client.patch(headset_url, json=dict(orientation=orientation))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == position
        assert headset2['orientation'] == orientation
        assert headset2['updated'] > headset['updated']

        # Test changing position and orientation
        position = dict(x=2, y=2, z=2)
        orientation = dict(x=1, y=0, z=0, w=0)
        response = await client.patch(headset_url, json=dict(position=position, orientation=orientation))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == position
        assert headset2['orientation'] == orientation
        assert headset2['updated'] > headset['updated']

        # Test GET headset returns an appropriate object
        response = await client.get(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2['position'] == position
        assert headset2['orientation'] == orientation
        assert headset2['updated'] > headset['updated']

        # Test pose changes returns all of the changes
        pose_changes_url = "/headsets/{}/pose-changes".format(headset['id'])
        response = await client.get(pose_changes_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        changes = await response.get_json()
        assert isinstance(changes, list)
        assert len(changes) == 3
        assert int(changes[0]['position']['x']) == 1
        assert int(changes[1]['orientation']['x']) == 1
        assert int(changes[2]['position']['x']) == 2

        # Test deleting the object
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
