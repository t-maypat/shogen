from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Campaign
from app.db.session import create_engine_for_url


def test_can_create_and_read_campaign(tmp_path) -> None:
    database_path = tmp_path / "shogen.db"
    engine = create_engine_for_url(f"sqlite+pysqlite:///{database_path}")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    assert {
        "campaigns",
        "workflow_runs",
        "stage_outputs",
        "creative_variants",
        "policy_findings",
        "approvals",
        "evaluation_results",
        "wave_proposals",
        "event_log",
    }.issubset(set(inspector.get_table_names()))

    brief = {
        "product_name": "NestWise",
        "product_category": "Fintech savings and starter investing app",
        "objective": "Drive qualified signups",
    }

    with Session(engine, expire_on_commit=False) as session:
        campaign = Campaign(
            name="NestWise Launch",
            status="draft",
            brief_json=brief,
        )
        session.add(campaign)
        session.commit()
        campaign_id = campaign.id

    with Session(engine) as session:
        stored_campaign = session.get(Campaign, campaign_id)

        assert stored_campaign is not None
        assert stored_campaign.name == "NestWise Launch"
        assert stored_campaign.tenant_id == "demo"
        assert stored_campaign.status == "draft"
        assert stored_campaign.brief_json["product_name"] == "NestWise"
