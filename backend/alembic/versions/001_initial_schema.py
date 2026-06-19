"""Initial schema — all tables, pgvector, FTS, RLS.

Revision ID: 001
Revises:
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ──
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── Enum types ──
    project_status = sa.Enum(
        "projectname", "collecting", "reviewing", "complete", name="project_status",
    )
    document_status = sa.Enum(
        "uploading", "chunking", "embedded", "ready", "error", name="document_status",
    )
    message_role = sa.Enum("user", "assistant", name="message_role")
    flag_type = sa.Enum("gap", "conflict", "missing", name="flag_type")
    analysis_status = sa.Enum("running", "complete", "error", name="analysis_status")

    # ── projects ──
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", project_status, nullable=False, server_default=sa.text("'collecting'")),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── documents ──
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text()),
        sa.Column("mime_type", sa.Text()),
        sa.Column("status", document_status, nullable=False, server_default=sa.text("'uploading'")),
    )

    # ── document_chunks ──
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("metadata", sa.JSON()),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
    )

    # FTS generated column + indexes
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_search_vector ON document_chunks "
        "USING gin (search_vector)"
    )

    # ── messages ──
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── dd_schema ──
    op.create_table(
        "dd_schema",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("fields", sa.JSON(), nullable=False),
    )

    # ── gap_flags ──
    op.create_table(
        "gap_flags",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.Text(), nullable=False),
        sa.Column("flag_type", flag_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), server_default=sa.text("false")),
    )

    # ── portfolio_profiles ──
    op.create_table(
        "portfolio_profiles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("portfolio_id", sa.Text(), nullable=False),
        sa.Column("portfolio_name", sa.Text(), nullable=False),
        sa.Column("investment_manager_name", sa.Text()),
        sa.Column("menu", sa.Text()),
        sa.Column("series_name", sa.Text()),
        sa.Column("inception_date", sa.DateTime(timezone=True)),
        sa.Column("asset_class", sa.Text()),
    )

    # ── analysis_outputs ──
    op.create_table(
        "analysis_outputs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("script_name", sa.Text(), nullable=False),
        sa.Column("output_path", sa.Text(), nullable=False),
        sa.Column("status", analysis_status, nullable=False, server_default=sa.text("'running'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── report_templates ──
    op.create_table(
        "report_templates",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── RLS ──
    _user_data_tables = [
        "projects", "documents", "document_chunks", "messages",
        "dd_schema", "gap_flags", "portfolio_profiles",
        "analysis_outputs", "report_templates",
    ]
    for table in _user_data_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # Projects: owner can see own rows
    op.execute(
        "CREATE POLICY projects_owner ON projects "
        "FOR ALL USING (user_id = auth.uid()::text)"
    )

    # All other tables: accessible if project belongs to user
    _child_tables = [t for t in _user_data_tables if t != "projects"]
    for table in _child_tables:
        op.execute(
            f"CREATE POLICY {table}_owner ON {table} "
            f"FOR ALL USING (project_id IN (SELECT id FROM projects WHERE user_id = auth.uid()::text))"
        )


def downgrade() -> None:
    _tables = [
        "report_templates", "analysis_outputs", "portfolio_profiles",
        "gap_flags", "dd_schema", "messages", "document_chunks",
        "documents", "projects",
    ]
    for table in _tables:
        op.drop_table(table)

    for enum_name in ["project_status", "document_status", "message_role", "flag_type", "analysis_status"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
