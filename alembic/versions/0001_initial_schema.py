"""Initial project workflow schema.

Revision ID: 0001
Revises:
Create Date: 2026-08-05
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("input_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("project_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
    )
    op.create_index("ix_projects_input_type", "projects", ["input_type"])
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "step_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_name", sa.String(length=80), nullable=False),
        sa.Column("queue_name", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_step_runs_project_id_projects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_step_runs"),
        sa.UniqueConstraint("project_id", "step_name", name="uq_step_runs_project_step"),
    )
    op.create_index("ix_step_runs_project_id", "step_runs", ["project_id"])
    op.create_index("ix_step_runs_status", "step_runs", ["status"])
    op.create_index("ix_step_runs_celery_task_id", "step_runs", ["celery_task_id"])
    op.create_index("ix_step_runs_scheduler", "step_runs", ["status", "queue_name", "created_at"])

    op.create_table(
        "step_dependencies",
        sa.Column("step_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_step_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["depends_on_step_run_id"], ["step_runs.id"], name="fk_step_dependencies_depends_on_step_run_id_step_runs", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_run_id"], ["step_runs.id"], name="fk_step_dependencies_step_run_id_step_runs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("step_run_id", "depends_on_step_run_id", name="pk_step_dependencies"),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artifact_type", sa.String(length=80), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("artifact_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_artifacts_project_id_projects", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_run_id"], ["step_runs.id"], name="fk_artifacts_step_run_id_step_runs", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_artifacts"),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])
    op.create_index("ix_artifacts_step_run_id", "artifacts", ["step_run_id"])
    op.create_index("ix_artifacts_project_type", "artifacts", ["project_id", "artifact_type"])


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("step_dependencies")
    op.drop_table("step_runs")
    op.drop_table("projects")
