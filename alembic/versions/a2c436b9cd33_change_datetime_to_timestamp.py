"""Change datetime to timestamp

Revision ID: a2c436b9cd33
Revises: c31c0586510f
Create Date: 2025-11-19 09:45:14.179470

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import TIMESTAMP


# revision identifiers, used by Alembic.
revision = 'a2c436b9cd33'
down_revision = 'c31c0586510f'
branch_labels = None
depends_on = None


# table name, column name, floating point precision
timestamp_changes = [
    ('incidents', 'created_time', None),
    ('incidents', 'updated_time', None),
    ('users', 'created_time', None),
    ('users', 'updated_time', None),
    ('streams', 'created_time', None),
    ('streams', 'updated_time', None),
    ('locations', 'created_time', None),
    ('locations', 'updated_time', None),
    ('layers', 'created_time', None),
    ('layers', 'updated_time', None),
    ('mobile_devices', 'created_time', None),
    ('mobile_devices', 'updated_time', None),
    ('tracking_sessions', 'created_time', None),
    ('tracking_sessions', 'updated_time', None),
    ('device_poses', 'created_time', 6),
    ('device_configurations', 'created_time', None),
    ('device_configurations', 'updated_time', None),
    ('map_markers', 'created_time', None),
    ('map_markers', 'updated_time', None),
    ('surfaces', 'created_time', 6),
    ('surfaces', 'updated_time', 6),
    ('photo_records', 'created_time', None),
    ('photo_records', 'updated_time', None),
    ('photo_files', 'created_time', None),
    ('photo_files', 'updated_time', None),
    ('detection_tasks', 'created_time', None),
    ('photo_annotations', 'created_time', None),
    ('map_paths', 'created_time', None),
]


def upgrade() -> None:
    for table, column, fsp in timestamp_changes:
        if column == 'created_time':
            op.alter_column(table, column, type_=TIMESTAMP(fsp=fsp), server_default=sa.text('CURRENT_TIMESTAMP'))
        elif column == 'updated_time':
            op.alter_column(table, column, type_=TIMESTAMP(fsp=fsp), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
        else:
            raise Exception("Not sure how to handle column {}.{}".format(table, column))


def downgrade() -> None:
    for table, column in timestamp_changes:
        if column == 'created_time':
            op.alter_column(table, column, type_=TIMESTAMP(fsp=fsp), server_default=sa.text('now()'))
        elif column == 'updated_time':
            op.alter_column(table, column, type_=TIMESTAMP(fsp=fsp), server_default=sa.text('now() ON UPDATE now()'))
        else:
            raise Exception("Not sure how to handle column {}.{}".format(table, column))
