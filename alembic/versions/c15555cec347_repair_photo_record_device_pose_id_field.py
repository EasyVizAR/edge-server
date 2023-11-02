"""Repair photo_record device_pose_id field

Revision ID: c15555cec347
Revises: b69392e30151
Create Date: 2023-11-02 10:51:45.044704

"""
import datetime
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c15555cec347'
down_revision = 'b69392e30151'
branch_labels = None
depends_on = None


# Maximum time difference between photo and device_pose
photo_match_max_time_difference = 15


def upgrade() -> None:
    conn = op.get_bind()

    fix_records = []
    query = sa.text('SELECT id, created_time, mobile_device_id FROM photo_records WHERE mobile_device_id IS NOT NULL AND location_id IS NOT NULL')
    res = conn.execute(query)
    for row in res.fetchall():
        fix_records.append(row)

    print("Found {} records to update".format(len(fix_records)))

    updates = []
    for record in fix_records:
        record_id, created_time, mobile_device_id = record

        query = sa.text("""
            SELECT id, tracking_session_id, 86400*abs(julianday(created_time) - julianday("{}")) as tdiff
            FROM device_poses
            WHERE mobile_device_id="{}"
            ORDER BY tdiff
            LIMIT 1
        """.format(created_time, mobile_device_id))
        res = conn.execute(query)
        result = res.fetchone()

        if result is not None and result[2] < photo_match_max_time_difference:
            updates.append((record_id, result[0], result[1]))

        else:
            updates.append((record_id, "NULL", "NULL"))

    for update in updates:
        query = sa.text("UPDATE photo_records SET device_pose_id={}, tracking_session_id={} WHERE id={}".format(update[1], update[2], update[0]))
        conn.execute(query)


def downgrade() -> None:
    pass
