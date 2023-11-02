import os

from http import HTTPStatus

import pytest

from server.main import app
from server.utils.testing import int_equal


@pytest.mark.asyncio
async def test_feature_routes():
    """
    Test feature routes
    """
    # Name of a field within the resource which we can change and test.
    test_field = "name"

    async with app.test_client() as client:
        # Create a test location
        response = await client.post("/locations", json=dict(name="Feature Test"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        location = await response.get_json()

        features_url = "/locations/{}/features".format(location['id'])

        # Initial list of features
        response = await client.get(features_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        features = await response.get_json()
        assert isinstance(features, list)

        # Initial list of features with envelope
        response = await client.get(features_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        features2 = await response.get_json()
        assert isinstance(features2, dict)
        assert isinstance(features2['items'], list)

        # Create an object
        response = await client.post(features_url, json={test_field: "foo"})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        feature = await response.get_json()
        assert isinstance(feature, dict)
        assert feature['id'] is not None
        assert feature[test_field] == "foo"

        feature_url = "{}/{}".format(features_url, feature['id'])

        # Test getting the object back
        response = await client.get(feature_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        feature2 = await response.get_json()
        assert int_equal(feature2['id'], feature['id'])
        assert feature2[test_field] == feature[test_field]

        # Test changing the name
        response = await client.patch(feature_url, json={"id": "bad", test_field: "bar"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        feature2 = await response.get_json()
        assert int_equal(feature2['id'], feature['id'])
        assert feature2[test_field] == "bar"

        # Test replacement
        response = await client.put(feature_url, json=feature)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        feature2 = await response.get_json()
        assert int_equal(feature2['id'], feature['id'])
        assert feature2[test_field] == feature[test_field]

        # Test deleting the object
        response = await client.delete(feature_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        feature2 = await response.get_json()
        assert int_equal(feature2['id'], feature['id'])

        # Test creating object through PUT
        response = await client.put(feature_url, json=feature)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        feature2 = await response.get_json()
        assert int_equal(feature2['id'], feature['id'])
        assert feature2[test_field] == feature[test_field]

        # Test that object does not exist after DELETE
        response = await client.delete(feature_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(feature_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(feature_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(feature_url, json={test_field: "bar"})
        assert response.status_code == HTTPStatus.NOT_FOUND

        # Clean up
        response = await client.delete('/locations/{}'.format(location['id']))
        assert response.status_code == HTTPStatus.OK
