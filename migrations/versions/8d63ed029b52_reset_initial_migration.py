"""Reset initial migration

Revision ID: 8d63ed029b52
Revises: 
Create Date: 2025-12-05 15:20:06.842411

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d63ed029b52'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('caregiver',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('caregiver_name', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('caregiver', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_caregiver_caregiver_name'), ['caregiver_name'], unique=True)
        batch_op.create_index(batch_op.f('ix_caregiver_email'), ['email'], unique=True)

    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=False),
    sa.Column('followed_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['followed_id'], ['caregiver.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['caregiver.id'], ),
    sa.PrimaryKeyConstraint('follower_id', 'followed_id')
    )
    op.create_table('symptom_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('diagnosis', sa.String(length=140), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('caregiver_id', sa.Integer(), nullable=False),
    sa.Column('severity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['caregiver_id'], ['caregiver.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('symptom_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_symptom_log_caregiver_id'), ['caregiver_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_symptom_log_timestamp'), ['timestamp'], unique=False)



def downgrade():
    with op.batch_alter_table('symptom_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_symptom_log_timestamp'))
        batch_op.drop_index(batch_op.f('ix_symptom_log_caregiver_id'))

    op.drop_table('symptom_log')
    op.drop_table('followers')
    with op.batch_alter_table('caregiver', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_caregiver_email'))
        batch_op.drop_index(batch_op.f('ix_caregiver_caregiver_name'))

    op.drop_table('caregiver')