"""Add streams table

Revision ID: 8c8743996966
Revises: c15555cec347
Create Date: 2023-11-29 14:35:32.561502

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c8743996966'
down_revision = 'c15555cec347'
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table('streams',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('publisher_addr', sa.String(), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('streams')
