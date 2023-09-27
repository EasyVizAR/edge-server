import os
import time
import uuid

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
        assert headset['token'] is not None

        headset_url = "{}/{}".format(headsets_url, headset['id'])

        # Test getting the object back
        response = await client.get(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2[test_field] == headset[test_field]

        # Test query by name
        response = await client.get(headsets_url + "?name={}".format(headset['name']))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        result = await response.get_json()
        assert isinstance(result, list)
        assert len(result) > 0

        # Test changing the name
        response = await client.patch(headset_url, json={"id": "bad", test_field: "bar"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']
        assert headset2[test_field] == "bar"

        # Test changing the location and querying for headsets at that location
        test_location_id = str(uuid.uuid4())
        response = await client.patch(headset_url, json={"location_id": test_location_id})
        assert response.status_code == HTTPStatus.OK
        response = await client.get("/headsets?location_id="+test_location_id)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headsets = await response.get_json()
        assert isinstance(headsets, list)
        assert headset['id'] in (h['id'] for h in headsets)

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
        test_location_id = str(uuid.uuid4())
        response = await client.post(headsets_url, json=dict(name="Test PUT", location_id=test_location_id))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['id'] is not None
        assert headset['name'] == "Test PUT"
        assert headset['location_id'] == test_location_id

        headset_url = "{}/{}".format(headsets_url, headset['id'])

        # Test changing position and orientation
        updated = headset.copy()
        updated['position'] = dict(x=1, y=1, z=1)
        updated['orientation'] = dict(x=0, y=0, z=0, w=1)
        response = await client.put(headset_url, json=updated)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset2, dict)
        assert headset2['id'] == headset['id']
        assert headset2['updated'] > updated['updated']
        assert headset2['location_id'] == test_location_id
        assert headset2['last_check_in_id'] > 0
        assert headset2['last_pose_change_id'] > 0

        # Test changing position and orientation
        updated = headset2.copy()
        updated['position'] = dict(x=2, y=1, z=1)
        updated['orientation'] = dict(x=0, y=0, z=1, w=0)
        response = await client.put(headset_url, json=updated)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset3 = await response.get_json()
        assert isinstance(headset3, dict)
        assert headset3['id'] == headset['id']
        assert headset3['updated'] > updated['updated']
        assert headset3['location_id'] == test_location_id
        assert headset3['last_check_in_id'] == headset2['last_check_in_id']
        assert headset3['last_pose_change_id'] > headset2['last_pose_change_id']

        # Test changing position and orientation
        updated = headset3.copy()
        updated['position'] = dict(x=1, y=3, z=1)
        updated['orientation'] = dict(x=0, y=1, z=0, w=0)
        response = await client.put(headset_url, json=updated)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset4 = await response.get_json()
        assert isinstance(headset4, dict)
        assert headset4['id'] == headset['id']
        assert headset4['updated'] > updated['updated']
        assert headset4['location_id'] == test_location_id
        assert headset4['last_check_in_id'] == headset2['last_check_in_id']
        assert headset4['last_pose_change_id'] > headset3['last_pose_change_id']

        # Test GET headset returns an appropriate object
        response = await client.get(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset5 = await response.get_json()
        assert headset5['id'] == headset['id']
        assert headset5['updated'] > headset['updated']
        assert headset5['location_id'] == test_location_id
        assert headset5['last_check_in_id'] == headset2['last_check_in_id']
        assert headset5['last_pose_change_id'] == headset4['last_pose_change_id']

        # Test pose changes returns all of the changes
        pose_changes_url = "/headsets/{}/pose-changes".format(headset['id'])
        response = await client.get(pose_changes_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        changes = await response.get_json()
        assert isinstance(changes, list)
        assert len(changes) == 3
        assert int(changes[0]['position']['x']) == 1
        assert int(changes[1]['position']['x']) == 2
        assert int(changes[2]['position']['x']) == 1
        assert int(changes[0]['orientation']['w']) == 1
        assert int(changes[1]['orientation']['w']) == 0
        assert int(changes[2]['orientation']['w']) == 0

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
        test_location_id = str(uuid.uuid4())
        response = await client.post(headsets_url, json=dict(name="Test PATCH", location_id=test_location_id))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)
        assert headset['id'] is not None
        assert headset['name'] == "Test PATCH"
        assert headset['position'] is not None
        assert headset['orientation'] is not None
        assert headset['location_id'] == test_location_id

        headset_url = "{}/{}".format(headsets_url, headset['id'])

        # Test changing position and orientation
        position = dict(x=1, y=1, z=1)
        orientation = dict(x=0, y=0, z=0, w=1)
        response = await client.patch(headset_url, json=dict(position=position, orientation=orientation))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == position
        assert headset2['orientation'] == orientation
        assert headset2['updated'] > headset['updated']

        # Test changing position and orientation
        position = dict(x=2, y=1, z=1)
        orientation = dict(x=0, y=0, z=0, w=0)
        response = await client.patch(headset_url, json=dict(position=position, orientation=orientation))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset, dict)
        assert headset2['id'] == headset['id']
        assert headset2['position'] == position
        assert headset2['orientation'] == orientation
        assert headset2['updated'] > headset['updated']

        # Test changing position and orientation
        position = dict(x=1, y=1, z=1)
        orientation = dict(x=0, y=0, z=0, w=0)
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
        assert int(changes[1]['position']['x']) == 2
        assert int(changes[2]['position']['x']) == 1
        assert int(changes[0]['orientation']['w']) == 1
        assert int(changes[1]['orientation']['w']) == 0
        assert int(changes[2]['orientation']['w']) == 0

        # Test deleting the object
        response = await client.delete(headset_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert headset2['id'] == headset['id']


@pytest.mark.asyncio
async def test_headset_incidents_tracking():
    """
    Test that server tracks list of incidents in which a headset is active.
    """
    async with app.test_client() as client:
        # Create a headset
        response = await client.post("/headsets", json=dict(name="Test Incidents"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        headset = await response.get_json()
        assert isinstance(headset, dict)

        # Create a new incident
        response = await client.post("/incidents", json=dict(name="Test Incident"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        incident = await response.get_json()
        assert isinstance(incident, dict)

        # List of active headsets should be empty
        response = await client.get("/incidents/active/headsets")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        active = await response.get_json()
        assert isinstance(active, list)
        assert len(active) == 0

        headset_url = "/headsets/{}".format(headset['id'])

        # Test changing headset location
        test_location_id = uuid.uuid4()
        response = await client.patch(headset_url, json=dict(location_id=test_location_id))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        headset2 = await response.get_json()
        assert isinstance(headset2, dict)

        # List of active headsets should contain the headset
        response = await client.get("/incidents/active/headsets")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        active = await response.get_json()
        assert isinstance(active, list)
        assert len(active) == 1
        assert active[0]['id'] == headset['id']

        # Clean up
        await client.delete(headset_url)
        await client.delete("/incidents/{}".format(incident['id']))
