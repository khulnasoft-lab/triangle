"""drop some indices

Revision ID: 017e0e81cb5c
Revises: 3ed780c856b2
Create Date: 2018-07-02 13:22:56.160433

"""

# revision identifiers, used by Alembic.
revision = '017e0e81cb5c'
down_revision = '3ed780c856b2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index(op.f('ix_sitetrace_full'), table_name='sitetrace')
    op.drop_index(op.f('ix_mastertrace_full'), table_name='mastertrace')


def downgrade():
    op.create_index(op.f('ix_mastertrace_full'), 'mastertrace', ['full'], unique=False)
    op.create_index(op.f('ix_sitetrace_full'), 'sitetrace', ['full'], unique=False)
