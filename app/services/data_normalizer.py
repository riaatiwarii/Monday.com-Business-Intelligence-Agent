from __future__ import annotations

import re
from datetime import datetime, timezone

import pandas as pd


def _norm_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _pick(record: dict, aliases: list[str]) -> str | None:
    values = record.get("values_by_title", {})
    normalized = {_norm_key(k): v for k, v in values.items()}
    for alias in aliases:
        val = normalized.get(_norm_key(alias))
        if val not in (None, "", "nan", "NaN"):
            return str(val).strip()
    return None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", value)
    if cleaned in ("", "-", "."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _to_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = pd.to_datetime(value, errors="coerce", utc=True)
    return None if pd.isna(dt) else dt.to_pydatetime().astimezone(timezone.utc)


def _probability_to_weight(value: str | None) -> float | None:
    if value is None:
        return None
    v = value.strip().lower()
    mapping = {
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "commit": 0.9,
        "closed won": 1.0,
    }
    if v in mapping:
        return mapping[v]
    pct = re.sub(r"[^0-9.]", "", v)
    if pct:
        try:
            n = float(pct)
            return n / 100.0 if n > 1 else n
        except ValueError:
            return None
    return None


def normalize_deals(records: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    caveats = []
    missing_probability = 0
    invalid_dates = 0

    for r in records:
        close_date = _to_dt(_pick(r, ["Close Date (A)", "Tentative Close Date"]))
        created_date = _to_dt(_pick(r, ["Created Date"]))
        if _pick(r, ["Close Date (A)", "Tentative Close Date"]) and close_date is None:
            invalid_dates += 1

        probability_raw = _pick(r, ["Closure Probability"])
        probability_weight = _probability_to_weight(probability_raw)
        if probability_weight is None:
            probability_weight = 0.5
            missing_probability += 1

        deal_value = _to_float(_pick(r, ["Masked Deal value", "Deal Value"])) or 0.0
        row = {
            "item_id": r.get("item_id"),
            "deal_name": r.get("item_name"),
            "owner_code": _pick(r, ["Owner code", "Owner"]),
            "client_code": _pick(r, ["Client Code"]),
            "deal_status": _pick(r, ["Deal Status"]) or "Unknown",
            "deal_stage": _pick(r, ["Deal Stage"]) or "Unknown",
            "sector": _pick(r, ["Sector/service", "Sector"]) or "Unknown",
            "close_date": close_date,
            "created_date": created_date,
            "closure_probability_raw": probability_raw,
            "probability_weight": probability_weight,
            "deal_value": deal_value,
            "weighted_value": deal_value * probability_weight,
        }
        rows.append(row)

    if missing_probability:
        caveats.append(
            f"{missing_probability} deal rows had missing/invalid closure probability; defaulted weight to 0.5."
        )
    if invalid_dates:
        caveats.append(
            f"{invalid_dates} deal rows had invalid date formats and were excluded from date-window filtering."
        )

    return pd.DataFrame(rows), caveats


def normalize_work_orders(records: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    caveats = []
    invalid_dates = 0

    for r in records:
        invoice_date_raw = _pick(r, ["Last invoice date", "Data Delivery Date", "Date of PO/LOI"])
        invoice_date = _to_dt(invoice_date_raw)
        if invoice_date_raw and invoice_date is None:
            invalid_dates += 1

        billed = _to_float(
            _pick(r, ["Billed Value in Rupees (Incl of GST.) (Masked)", "Billed Value in Rupees (Excl of GST.) (Masked)"])
        ) or 0.0
        collected = _to_float(_pick(r, ["Collected Amount in Rupees (Incl of GST.) (Masked)"])) or 0.0
        receivable = _to_float(_pick(r, ["Amount Receivable (Masked)"]))
        if receivable is None:
            receivable = max(billed - collected, 0.0)

        row = {
            "item_id": r.get("item_id"),
            "work_order_name": r.get("item_name"),
            "owner_code": _pick(r, ["BD/KAM Personnel code", "Owner code"]),
            "sector": _pick(r, ["Sector", "Sector/service"]) or "Unknown",
            "wo_status": _pick(r, ["WO Status (billed)", "Execution Status"]) or "Unknown",
            "invoice_status": _pick(r, ["Invoice Status"]) or "Unknown",
            "billing_status": _pick(r, ["Billing Status"]) or "Unknown",
            "collection_status": _pick(r, ["Collection status"]) or "Unknown",
            "invoice_date": invoice_date,
            "billed_value": billed,
            "collected_value": collected,
            "receivable_value": receivable,
        }
        rows.append(row)

    if invalid_dates:
        caveats.append(
            f"{invalid_dates} work-order rows had invalid date formats and were excluded from date-window filtering."
        )

    return pd.DataFrame(rows), caveats
