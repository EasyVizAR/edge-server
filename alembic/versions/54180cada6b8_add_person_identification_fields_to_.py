"""Add person identification fields to photo_annotations

Revision ID: 54180cada6b8
Revises: 8c8743996966
Create Date: 2024-02-13 11:16:55.067268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54180cada6b8'
down_revision = '8c8743996966'
branch_labels = None
depends_on = None

naming_convention = {
    "fk":
    "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade() -> None:
    # The photo_records table has some foreign keys that point to non-existant tables.
    # In order to safely correct them, we need to create temporary tables with the
    # offending names in order to modify photo_records.
    op.create_table('tracking_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('queues',
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('name')
    )

    with op.batch_alter_table("photo_records", naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint("fk_photo_records_tracking_session_id_tracking_session", type_="foreignkey")
        batch_op.drop_constraint("fk_photo_records_queue_name_queues", type_="foreignkey")

        batch_op.create_foreign_key("fk_tracking_session", "tracking_sessions", ["tracking_session_id"], ["id"], ondelete="SET NULL", onupdate="CASCADE")
        batch_op.create_foreign_key("fk_photo_queue", "photo_queues", ["queue_name"], ["name"], ondelete="SET NULL", onupdate="CASCADE")

    op.drop_table('queues')
    op.drop_table('tracking_session')

    with op.batch_alter_table("photo_annotations", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("identified_user_id", sa.Uuid(), nullable=True), insert_after="detection_task_id")
        batch_op.add_column(sa.Column("sublabel", sa.String(), default="", nullable=False), insert_after="label")

    photo_queues = [{
        'name': 'identification',
        'next_queue_name': 'done',
        'display_order': 25,
        'description': 'The photo will be processed by a face recognition module.'
    }]

    meta = sa.MetaData()
    meta.reflect(bind=op.get_bind(), only=('photo_queues',))
    table = sa.Table('photo_queues', meta)
    op.bulk_insert(table, photo_queues)


def downgrade() -> None:
    op.drop_column("photo_annotations", "identified_user_id")
    op.drop_column("photo_annotations", "sublabel")
