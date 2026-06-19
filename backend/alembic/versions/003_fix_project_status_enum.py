"""Remove spurious 'projectname' value from project_status enum.

Revision ID: 003
Revises: 002
Create Date: 2026-06-11
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safety: ensure no rows carry the bad value before we drop it
    op.execute("UPDATE projects SET status = 'collecting' WHERE status::text = 'projectname'")

    # Must drop the server_default before altering the column type, then restore it
    op.execute("ALTER TABLE projects ALTER COLUMN status DROP DEFAULT")

    # Postgres doesn't allow removing enum values — recreate the type
    op.execute("ALTER TYPE project_status RENAME TO project_status_old")
    op.execute("CREATE TYPE project_status AS ENUM ('collecting', 'reviewing', 'complete')")
    op.execute(
        "ALTER TABLE projects ALTER COLUMN status TYPE project_status "
        "USING status::text::project_status"
    )
    op.execute("DROP TYPE project_status_old")

    # Restore the default
    op.execute("ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'collecting'")


def downgrade() -> None:
    op.execute("ALTER TABLE projects ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE project_status RENAME TO project_status_new")
    op.execute(
        "CREATE TYPE project_status AS ENUM ('projectname', 'collecting', 'reviewing', 'complete')"
    )
    op.execute(
        "ALTER TABLE projects ALTER COLUMN status TYPE project_status "
        "USING status::text::project_status"
    )
    op.execute("DROP TYPE project_status_new")
    op.execute("ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'collecting'")
