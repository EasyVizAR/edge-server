import pytest

from http import HTTPStatus

from server.main import app


@pytest.mark.asyncio
async def test_handlers():
    """
    Test handlers
    """
    async with app.test_client() as client:
        data = {
            "call": "play",
            "addr": "0.0.0.0",
            "app": "test",
            "name": "test"
        }

        response = await client.post("/streams/on_play", data=data)
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = await client.post("/streams/on_play_done", data=data)
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = await client.post("/streams/on_publish", data=data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        response = await client.post("/streams/on_publish_done", data=data)
        assert response.status_code == HTTPStatus.NO_CONTENT
