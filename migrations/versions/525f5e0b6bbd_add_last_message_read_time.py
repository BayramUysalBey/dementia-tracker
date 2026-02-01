"""add last_message_read_time

Revision ID: 525f5e0b6bbd
Revises: ae4de4539306
Create Date: 2025-12-12 15:54:55.470248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '525f5e0b6bbd'
down_revision = 'ae4de4539306'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.Float(), nullable=False),
    sa.Column('payload_json', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['caregiver.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notification_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_notification_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_notification_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('caregiver', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_message_read_time', sa.DateTime(), nullable=True))

    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('diagnosis', sa.String(length=140), nullable=False))
        batch_op.drop_column('body')


def downgrade():
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('body', sa.VARCHAR(length=140), autoincrement=False, nullable=False))
        batch_op.drop_column('diagnosis')

    with op.batch_alter_table('caregiver', schema=None) as batch_op:
        batch_op.drop_column('last_message_read_time')

    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notification_user_id'))
        batch_op.drop_index(batch_op.f('ix_notification_timestamp'))
        batch_op.drop_index(batch_op.f('ix_notification_name'))

    op.drop_table('notification')
