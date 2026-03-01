from datetime import datetime, timezone

import pandas as pd

from app.services.bi_engine import BIEngine


def test_compute_deals_basic():
    df = pd.DataFrame(
        [
            {
                "deal_status": "Open",
                "deal_value": 100.0,
                "weighted_value": 50.0,
                "sector": "Mining",
                "deal_stage": "SQL",
                "owner_code": "OWNER_001",
                "close_date": datetime.now(timezone.utc),
            },
            {
                "deal_status": "Won",
                "deal_value": 80.0,
                "weighted_value": 80.0,
                "sector": "Mining",
                "deal_stage": "Proposal",
                "owner_code": "OWNER_001",
                "close_date": datetime.now(timezone.utc),
            },
        ]
    )

    metrics = BIEngine().compute_deals(df, sector="Mining", owner_code=None, start_date=None, end_date=None)
    assert metrics["open_pipeline_value"] == 100.0
    assert metrics["weighted_pipeline_value"] == 50.0
    assert metrics["won_value"] == 80.0


def test_compute_work_orders_basic():
    df = pd.DataFrame(
        [
            {
                "billed_value": 200.0,
                "collected_value": 100.0,
                "receivable_value": 100.0,
                "sector": "Powerline",
                "owner_code": "OWNER_002",
                "invoice_date": datetime.now(timezone.utc),
            }
        ]
    )

    metrics = BIEngine().compute_work_orders(df, sector="Powerline", owner_code=None, start_date=None, end_date=None)
    assert metrics["billed_total"] == 200.0
    assert metrics["collected_total"] == 100.0
    assert metrics["receivable_total"] == 100.0
    assert metrics["collection_efficiency_pct"] == 50.0
