import json
import os
import secrets

from functools import wraps

import sqlalchemy as sa

from quart import g, request, websocket
from werkzeug.exceptions import Unauthorized

from server.models.mobile_devices import MobileDevice


class Authenticator:
    def __init__(self):
        self.tokens = []
        self.headsets = dict()
        self.path = "auth.json"

        self.cache = dict()

    def create_temporary_token(self, bearer_id):
        """
        Create a temporary token that will last until system shutdown.
        """
        token = secrets.token_urlsafe(16)
        self.cache[token] = bearer_id
        return token

    async def find_device_by_token(self, token):
        async with g.session_maker() as session:
            stmt = sa.select(MobileDevice) \
                    .where(MobileDevice.token == token) \
                    .limit(1)
            result = await session.execute(stmt)
            return result.scalar()

    async def lookup_token(self, token):
        if token in self.cache:
            g.headset_id, g.user_id = self.cache[token]
            return True

        device = await self.find_device_by_token(token)
        if device is not None:
            g.headset_id = device.id
            g.user_id = None
            self.cache[token] = (device.id, None)
            return True

        return False

    async def authenticate_request(self):
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) >= 2 and parts[0] == "Bearer":
            await self.lookup_token(parts[1])

    async def authenticate_websocket(self):
        # This is one way to do websocket authentication, check the HTTP
        # Authorization header.  There is another path that sets
        # websockets.authorization username and password and maybe other
        # fields.
        auth = websocket.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) >= 2 and parts[0] == "Bearer":
            await self.lookup_token(parts[1])

    @classmethod
    def build_authenticator(_class, data_dir):
        auth = _class()
        auth.path = os.path.join(data_dir, "auth.json")

        try:
            with open(auth.path, "r") as source:
                data = json.load(source)
                for item in data:
                    auth.tokens.append(item)
                    if item['type'] == 'headset':
                        auth.headsets[item['token']] = item
        except Exception as error:
            print("Warning: failed to load {} ({})".format(auth.path, error))

        return auth


def requires_own_headset_id(func):
    """
    Decorate an API call that only be called by the owning headset.

    Example: POST /headsets/{x}/check-ins may only be called by headset x or
    perhaps an administrator but importantly, no other headsets.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        g.authenticator.authenticate_request()

        required_headset_id = kwargs.get('headset_id')
        if required_headset_id is not None and required_headset_id != g.headset_id:
            raise Unauthorized("Only headset {} may make this request".format(required_headset_id))

        return await func(*args, **kwargs)

    return wrapper
