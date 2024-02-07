"""Add parsed trace content columns

Revision ID: d59c21eaa9e6
Revises: 50f677311842
Create Date: 2017-09-15 18:48:08.396809

"""

# revision identifiers, used by Alembic.
revision = 'd59c21eaa9e6'
down_revision = '50f677311842'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column(
        'mastertrace',
        sa.Column( 'content', postgresql.JSONB())
    )
    op.add_column(
        'sitetrace',
        sa.Column('content', postgresql.JSONB())
    )
    op.add_column(
        'sitealiasmastertrace',
        sa.Column('content', postgresql.JSONB())
    )


def downgrade():
    op.drop_column('mastertrace', 'content')
    op.drop_column('sitetrace', 'content')
    op.drop_column('sitealiasmastertrace', 'content')
