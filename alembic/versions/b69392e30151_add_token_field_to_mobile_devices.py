"""Add token field to mobile devices

Revision ID: b69392e30151
Revises: 682684a1c52c
Create Date: 2023-11-01 14:24:57.881972

"""
import secrets

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b69392e30151'
down_revision = '682684a1c52c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, add the token column.
    with op.batch_alter_table("mobile_devices", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("token", sa.String(), default="NONE", nullable=False), insert_after="color")

    # Then set a unique token for each device.
    conn = op.get_bind()
    query = sa.text('SELECT id FROM mobile_devices WHERE token=="NONE"')
    res = conn.execute(query)
    for row in res.fetchall():
        op.execute('UPDATE mobile_devices SET token="{}" WHERE id="{}"'.format(secrets.token_urlsafe(16), row[0]))

    # Finally, we can add a uniqueness constraint on the token column.
    # This should also index the table, which will be good for quick authentications.
    with op.batch_alter_table("mobile_devices", recreate="always") as batch_op:
        batch_op.create_unique_constraint("uq_token", ["token"])


def downgrade() -> None:
    op.drop_column("mobile_devices", "token")
