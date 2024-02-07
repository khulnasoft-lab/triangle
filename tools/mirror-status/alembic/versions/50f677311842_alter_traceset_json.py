"""Alter traceset column to type jsonb

Revision ID: 50f677311842
Revises: 39d1d907980a
Create Date: 2017-09-15 18:21:59.034255

"""

# revision identifiers, used by Alembic.
revision = '50f677311842'
down_revision = '39d1d907980a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.alter_column(
        table_name='traceset',
        column_name='traceset',
        type_=postgresql.JSONB(),
        postgresql_using='traceset::jsonb',
    )


def downgrade():
    op.alter_column(
        table_name='traceset',
        column_name='traceset',
        type_=sa.String(),
        postgresql_using='traceset::text',
    )
