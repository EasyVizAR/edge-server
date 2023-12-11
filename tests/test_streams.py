import uuid

import pytest

from http import HTTPStatus

from server.main import app


@pytest.mark.asyncio
async def test_handlers():
    """
    Test handlers called by nginx-rtmp module
    """
    async with app.test_client() as client:
        stream_id = uuid.uuid4()

        data = {
            "addr": "0.0.0.0",
            "app": "test",
            "name": str(stream_id)
        }

        data['call'] = "play"
        response = await client.post("/streams/on_play", form=data)
        assert response.status_code == HTTPStatus.NO_CONTENT

        data['call'] = "on_play_done"
        response = await client.post("/streams/on_play_done", form=data)
        assert response.status_code == HTTPStatus.NO_CONTENT

        data['call'] = "on_publish"
        response = await client.post("/streams/on_publish", form=data)
        assert response.status_code == HTTPStatus.FORBIDDEN

        data['call'] = "on_publish_done"
        response = await client.post("/streams/on_publish_done", form=data)
        assert response.status_code == HTTPStatus.NO_CONTENT
