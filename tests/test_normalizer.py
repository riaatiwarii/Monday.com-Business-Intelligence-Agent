from app.services.data_normalizer import normalize_deals, normalize_work_orders


def test_normalize_deals_defaults_probability():
    records = [
        {
            "item_id": "1",
            "item_name": "Deal A",
            "values_by_title": {
                "Deal Status": "Open",
                "Masked Deal value": "1000",
                "Sector/service": "Mining",
            },
        }
    ]
    df, caveats = normalize_deals(records)
    assert len(df) == 1
    assert float(df.iloc[0]["probability_weight"]) == 0.5
    assert len(caveats) == 1


def test_normalize_work_orders_receivable_fallback():
    records = [
        {
            "item_id": "2",
            "item_name": "WO A",
            "values_by_title": {
                "Billed Value in Rupees (Incl of GST.) (Masked)": "2000",
                "Collected Amount in Rupees (Incl of GST.) (Masked)": "500",
                "Sector": "Powerline",
            },
        }
    ]
    df, _ = normalize_work_orders(records)
    assert len(df) == 1
    assert float(df.iloc[0]["receivable_value"]) == 1500.0
