import datetime
import uuid

from http import HTTPStatus

import sqlalchemy as sa

import marshmallow
from quart import Blueprint, current_app, g, jsonify, request, send_from_directory
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from werkzeug import exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from server import auth
from server.models.users import User
from server.utils.response import maybe_wrap


class UserSchema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = auto_field(description="User ID (UUID)")

    name = auto_field(description="User name (must be unique)")
    display_name = auto_field(description="User display name")
    type = auto_field(description="User type (admin|user)")

    created_time = auto_field(description="Time the user was created")
    updated_time = auto_field(description="Last time the user was updated")


users = Blueprint('users', __name__)
user_schema = UserSchema()


@users.route('/users', methods=['GET'])
async def list_users():
    items = []

    stmt = sa.select(User)
    result = await g.session.execute(stmt)
    for row in result.scalars():
        items.append(user_schema.dump(row))

    return jsonify(maybe_wrap(items)), HTTPStatus.OK


@users.route('/users', methods=['POST'])
@auth.requires_admin
async def create_user():
    body = await request.get_json()
    if body is None:
        body = dict()
    body['id'] = uuid.uuid4()

    user = user_schema.load(body, transient=True, unknown=marshmallow.EXCLUDE)
    if 'password' in body:
        user.password = generate_password_hash(body['password'])

    g.session.add(user)
    await g.session.commit()

    result = user_schema.dump(user)

    return jsonify(result), HTTPStatus.CREATED


@users.route('/users/<uuid:user_id>', methods=['GET'])
async def get_user(user_id):
    stmt = sa.select(User) \
            .where(User.id == user_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    user = result.scalar()
    if user is None:
        raise exceptions.NotFound(description="User {} was not found".format(user_id))

    result = user_schema.dump(user)

    return jsonify(result), HTTPStatus.OK


@users.route('/users/<uuid:user_id>', methods=['PATCH'])
@auth.requires_admin
async def update_user(user_id):
    body = await request.get_json()

    stmt = sa.select(User) \
            .where(User.id == user_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    user = result.scalar()
    if user is None:
        raise exceptions.NotFound(description="User {} was not found".format(user_id))

    user.update(body)
    if 'password' in body:
        user.password = generate_password_hash(body['password'])
    user.updated_time = datetime.datetime.now()
    await g.session.commit()

    result = user_schema.dump(user)

    return jsonify(result), HTTPStatus.OK


@users.route('/users/<uuid:user_id>', methods=['DELETE'])
@auth.requires_admin
async def delete_user(user_id):
    stmt = sa.select(User) \
            .where(User.id == user_id) \
            .limit(1)

    result = await g.session.execute(stmt)
    user = result.scalar()
    if user is None:
        raise exceptions.NotFound(description="User {} was not found".format(user_id))

    await g.session.delete(user)
    await g.session.commit()

    result = user_schema.dump(user)

    return jsonify(result), HTTPStatus.OK
