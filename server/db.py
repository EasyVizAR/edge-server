"""
Database management utility
"""

import argparse
import secrets
import sys

import sqlalchemy as sa
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from server.models.base import Base
from server.models.users import User


sqlite_file = "easyvizar-edge.sqlite"

engine = create_engine("sqlite:///"+sqlite_file)
session_maker = sessionmaker(bind=engine)


def set_admin_password(password=None):
    if password is None or len(password) == 0:
        password = secrets.token_urlsafe(12)

    with session_maker() as session:
        # Make sure an admin account exists
        stmt = sa.select(User) \
                .where(User.name == "admin") \
                .limit(1)
        result = session.execute(stmt)
        admin = result.scalar()

    if admin is None:
        admin = User(
            id=uuid.uuid4(),
            name="admin",
            password=generate_password_hash(password),
            display_name="Default Admin",
            type="admin"
        )
        session.add(admin)
        print(f'*** Generated admin user ({admin.id}) with name "{admin.name}" and password "{password}" ***')
    else:
        admin.password = generate_password_hash(password)
        print(f'*** Updated admin user ({admin.id}) with name "{admin.name}" and password "{password}" ***')

    session.flush()


def main():
    parser = argparse.ArgumentParser(prog="db", description="EasyVizAR database management utility")
    subparsers = parser.add_subparsers(dest="command")

    sap_parser = subparsers.add_parser("set-admin-password", help="Set the admin user password")
    sap_parser.add_argument("password", type=str, default="", nargs="?", help="New password, default is random")

    args = parser.parse_args()

    if args.command == "set-admin-password":
        set_admin_password(args.password)


if __name__ == "__main__":
    main()
