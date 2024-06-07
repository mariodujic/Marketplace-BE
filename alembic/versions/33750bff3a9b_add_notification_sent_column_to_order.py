"""Add notification_sent column to Order

Revision ID: 33750bff3a9b
Revises: 
Create Date: 2024-06-07 14:34:16.511331

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '33750bff3a9b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('order', sa.Column('notification_sent', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('order', 'notification_sent')
