"""Alter aliases column to type jsonb

Revision ID: 3ed780c856b2
Revises: 0eb8618a233d
Create Date: 2017-09-24 12:43:16.611260

"""

# revision identifiers, used by Alembic.
revision = '3ed780c856b2'
down_revision = '0eb8618a233d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.alter_column(
        table_name='checkoverview',
        column_name='aliases',
        type_=postgresql.JSONB(),
        postgresql_using='aliases::jsonb',
    )


def downgrade():
    op.alter_column(
        table_name='checkoverview',
        column_name='aliases',
        type_=sa.String(),
        postgresql_using='aliases::text',
    )
