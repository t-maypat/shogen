"""Create the initial Shogen backend schema."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260621_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

jsonb_type = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Text(), server_default=sa.text("'demo'"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("brief_json", jsonb_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "CREATE INDEX campaigns_tenant_created_idx "
        "ON campaigns (tenant_id, created_at DESC)"
    )
    op.create_index("campaigns_status_idx", "campaigns", ["status"], unique=False)

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("current_stage", sa.Text(), nullable=True),
        sa.Column("revision_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("replay_mode", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("error_json", jsonb_type, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "CREATE INDEX workflow_runs_campaign_created_idx "
        "ON workflow_runs (campaign_id, created_at DESC)"
    )
    op.create_index("workflow_runs_status_idx", "workflow_runs", ["status"], unique=False)

    op.create_table(
        "stage_outputs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("stage_name", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("output_json", jsonb_type, nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "stage_name",
            "schema_version",
            name="stage_outputs_run_stage_schema_key",
        ),
    )

    op.create_table(
        "creative_variants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("persona_id", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("journey_stage", sa.Text(), nullable=False),
        sa.Column("primary_kpi", sa.Text(), nullable=False),
        sa.Column("revision_number", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("copy_json", jsonb_type, nullable=False),
        sa.Column("parent_variant_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["parent_variant_id"], ["creative_variants.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("creative_campaign_idx", "creative_variants", ["campaign_id"], unique=False)
    op.create_index(
        "creative_persona_channel_idx",
        "creative_variants",
        ["campaign_id", "persona_id", "channel"],
        unique=False,
    )
    op.create_index("creative_status_idx", "creative_variants", ["status"], unique=False)

    op.create_table(
        "policy_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("rule_id", sa.Text(), nullable=True),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("finding_type", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("metadata_json", jsonb_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["creative_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("persona_id", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("scores_json", jsonb_type, nullable=False),
        sa.Column("total_score", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["creative_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "wave_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_json", jsonb_type, nullable=False),
        sa.Column("rationale_json", jsonb_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "event_log",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
            autoincrement=True,
        ),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=True),
        sa.Column("payload_json", jsonb_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("event_log_campaign_id_idx", "event_log", ["campaign_id", "id"], unique=False)
    op.create_index("event_log_run_id_idx", "event_log", ["run_id", "id"], unique=False)


def downgrade() -> None:
    op.drop_index("event_log_run_id_idx", table_name="event_log")
    op.drop_index("event_log_campaign_id_idx", table_name="event_log")
    op.drop_table("event_log")
    op.drop_table("wave_proposals")
    op.drop_table("evaluation_results")
    op.drop_table("approvals")
    op.drop_table("policy_findings")
    op.drop_index("creative_status_idx", table_name="creative_variants")
    op.drop_index("creative_persona_channel_idx", table_name="creative_variants")
    op.drop_index("creative_campaign_idx", table_name="creative_variants")
    op.drop_table("creative_variants")
    op.drop_table("stage_outputs")
    op.drop_index("workflow_runs_status_idx", table_name="workflow_runs")
    op.execute("DROP INDEX workflow_runs_campaign_created_idx")
    op.drop_table("workflow_runs")
    op.drop_index("campaigns_status_idx", table_name="campaigns")
    op.execute("DROP INDEX campaigns_tenant_created_idx")
    op.drop_table("campaigns")
