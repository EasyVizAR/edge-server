import os

from http import HTTPStatus

import pytest

from server.main import app


@pytest.mark.asyncio
async def test_annotation_routes():
    """
    Test annotation routes
    """
    # Name of a field within the resource which we can change and test.
    test_field = "label"

    async with app.test_client() as client:
        # Create a test photo
        response = await client.post("/photos", json=dict(contentType="image/jpeg"))
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        photo = await response.get_json()

        annotations_url = "/photos/{}/annotations".format(photo['id'])

        # Initial list of annotations
        response = await client.get(annotations_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        annotations = await response.get_json()
        assert isinstance(annotations, list)

        # Initial list of annotations with envelope
        response = await client.get(annotations_url + "?envelope=items")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        annotations2 = await response.get_json()
        assert isinstance(annotations2, dict)
        assert isinstance(annotations2['items'], list)

        # Create an object
        response = await client.post(annotations_url, json={test_field: "foo"})
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        annotation = await response.get_json()
        assert isinstance(annotation, dict)
        assert annotation['id'] is not None
        assert annotation[test_field] == "foo"

        annotation_url = "{}/{}".format(annotations_url, annotation['id'])

        # Test getting the object back
        response = await client.get(annotation_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        annotation2 = await response.get_json()
        assert annotation2['id'] == annotation['id']
        assert annotation2[test_field] == annotation[test_field]

        # Test changing a field
        response = await client.patch(annotation_url, json={"id": "bad", test_field: "bar"})
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        annotation2 = await response.get_json()
        assert annotation2['id'] == annotation['id']
        assert annotation2[test_field] == "bar"

        # Test replacement
        response = await client.put(annotation_url, json=annotation)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        annotation2 = await response.get_json()
        assert annotation2['id'] == annotation['id']
        assert annotation2[test_field] == annotation[test_field]

        # Test deleting the object
        response = await client.delete(annotation_url)
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        annotation2 = await response.get_json()
        assert annotation2['id'] == annotation['id']

        # Test creating object through PUT
        response = await client.put(annotation_url, json=annotation)
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json
        annotation2 = await response.get_json()
        assert annotation2['id'] == annotation['id']
        assert annotation2[test_field] == annotation[test_field]

        # Test that object does not exist after DELETE
        response = await client.delete(annotation_url)
        assert response.status_code == HTTPStatus.OK
        response = await client.delete(annotation_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.get(annotation_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        response = await client.patch(annotation_url, json={test_field: "bar"})
        assert response.status_code == HTTPStatus.NOT_FOUND
