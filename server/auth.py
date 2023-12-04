import json
import os
import secrets
import uuid

from functools import wraps

import sqlalchemy as sa

from quart import g, request, websocket, after_this_request, current_app
from werkzeug.exceptions import Unauthorized
from werkzeug.security import check_password_hash, generate_password_hash

from server.models.mobile_devices import MobileDevice
from server.models.users import User


class Authenticator:
    def __init__(self):
        self.tokens = []
        self.headsets = dict()
        self.path = "auth.json"

        self.cache = dict()
        self.user_cache = dict()

    def create_temporary_token(self, bearer_id):
        """
        Create a temporary token that will last until system shutdown.
        """
        token = secrets.token_urlsafe(16)
        self.cache[token] = bearer_id
        return token

    async def find_device_by_token(self, token):
        stmt = sa.select(MobileDevice) \
                .where(MobileDevice.token == token) \
                .limit(1)
        result = await g.session.execute(stmt)
        return result.scalar()

    async def lookup_token(self, token):
        if token in self.cache:
            g.device_id, g.user_id = self.cache[token]
            return True

        device = await self.find_device_by_token(token)
        if device is not None:
            g.device_id = device.id
            g.user_id = None
            g.user = None
            self.cache[token] = (device.id, None)
            return True

        return False

    async def lookup_user(self, username, password):
        stmt = sa.select(User) \
                .where(User.name == username) \
                .limit(1)
        result = await g.session.execute(stmt)
        user = result.scalar()
        if user is not None and check_password_hash(user.password, password):
            return user
        else:
            return None

    async def authenticate_request(self):
        # If we have a valid user_session cookie, we can skip the DB lookup and
        # password hash check.
        token = request.cookies.get("user_session")
        if token is not None and token in self.user_cache:
            g.user = self.user_cache[token]
            g.user_id = g.user.id
            return

        # Basic auth path, ie. username and password.
        if request.authorization is not None:
            username = request.authorization.get("username")
            password = request.authorization.get("password")
            user = await self.lookup_user(username, password)

            if user is not None:
                token = secrets.token_urlsafe(16)
                self.user_cache[token] = user

                # Return a user_session token cookie with the response to this
                # request.  If the client browser sends that cookie, we can
                # avoid DB lookups on future requests.
                @after_this_request
                def after_index(response):
                    response.set_cookie("user_session", token)
                    return response

                g.user_id = user.id
                g.user = user

        # Bearer token, for authenticated devices.
        else:
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


async def initialize_users_table(app):
    async with app.session_maker() as session:
        # Make sure an admin account exists
        stmt = sa.select(User) \
                .where(User.name == "admin") \
                .limit(1)
        result = await session.execute(stmt)
        admin = result.scalar()

        if admin is None:
            admin = User(
                id=uuid.uuid4(),
                name="admin",
                password=generate_password_hash("admin"),
                display_name="Default Admin",
                type="admin"
            )
            session.add(admin)

        # Make sure a default user account exists
        stmt = sa.select(User) \
                .where(User.name == "user") \
                .limit(1)
        result = await session.execute(stmt)
        user = result.scalar()

        if user is None:
            user = User(
                id=uuid.uuid4(),
                name="user",
                password=generate_password_hash(""),
                display_name="Default User",
                type="user"
            )
            session.add(user)

        # Make sure a guest user account exists
        stmt = sa.select(User) \
                .where(User.name == "guest") \
                .limit(1)
        result = await session.execute(stmt)
        guest = result.scalar()

        if guest is None:
            guest = User(
                id=uuid.uuid4(),
                name="guest",
                password=generate_password_hash(""),
                display_name="Guest",
                type="user"
            )
            session.add(guest)

        await session.commit()

        # Save the default user ID to use as a placeholder when the user ID is
        # unknown
        app.default_user_id = user.id


def requires_admin(func):
    """
    Decorate an endpoint that can only be called by a logged-in admin user.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # authenticate_request is called on all requests, so this is redundant
        #await g.authenticator.authenticate_request()

        # The easiest way to keep our tests working is to set an environment
        # variable to disable authentication during testing. The drawback is,
        # of course, authentication does not get tested.
        not_in_testing = current_app.config.get("ENV", "production") != "testing"

        if not_in_testing and (g.user is None or g.user.type != "admin"):
            authenticate = ('Basic realm="Admin access to EasyVizAR Edge", charset="UTF-8"',)
            raise Unauthorized(www_authenticate=authenticate)

        return await func(*args, **kwargs)

    return wrapper


def requires_user(func):
    """
    Decorate an endpoint that can only be called by a logged-in user.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # authenticate_request is called on all requests, so this is redundant
        #await g.authenticator.authenticate_request()

        # The easiest way to keep our tests working is to set an environment
        # variable to disable authentication during testing. The drawback is,
        # of course, authentication does not get tested.
        not_in_testing = current_app.config.get("ENV", "production") != "testing"

        if not_in_testing and g.user_id is None:
            authenticate = ('Basic realm="Access to EasyVizAR Edge", charset="UTF-8"',)
            raise Unauthorized(www_authenticate=authenticate)

        return await func(*args, **kwargs)

    return wrapper


def requires_own_headset_id(func):
    """
    Decorate an API call that only be called by the owning headset.

    Example: POST /headsets/{x}/check-ins may only be called by headset x or
    perhaps an administrator but importantly, no other headsets.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # authenticate_request is called on all requests, so this is redundant
        #await g.authenticator.authenticate_request()

        required_headset_id = kwargs.get('headset_id')
        if required_headset_id is not None and required_headset_id != g.device_id:
            raise Unauthorized("Only headset {} may make this request".format(required_headset_id))

        return await func(*args, **kwargs)

    return wrapper
