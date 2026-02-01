"""private messages

Revision ID: ae4de4539306
Revises: 8d63ed029b52
Create Date: 2025-12-11 13:56:06.932031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae4de4539306'
down_revision = '8d63ed029b52'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['caregiver.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['caregiver.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_message_recipient_id'), ['recipient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_message_sender_id'), ['sender_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_message_timestamp'), ['timestamp'], unique=False)

    op.execute("UPDATE symptom_log SET severity = 1 WHERE severity IS NULL")

    with op.batch_alter_table('symptom_log', schema=None) as batch_op:
        batch_op.alter_column('severity',
               existing_type=sa.INTEGER(),
               nullable=False)



def downgrade():
    with op.batch_alter_table('symptom_log', schema=None) as batch_op:
        batch_op.alter_column('severity',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_message_timestamp'))
        batch_op.drop_index(batch_op.f('ix_message_sender_id'))
        batch_op.drop_index(batch_op.f('ix_message_recipient_id'))

    op.drop_table('message')
