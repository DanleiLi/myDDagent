"""Add converted_path to documents.

Revision ID: 002
Revises: 001
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("converted_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "converted_path")
