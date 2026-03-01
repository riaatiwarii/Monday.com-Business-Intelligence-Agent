from __future__ import annotations

from datetime import datetime

import pandas as pd


class BIEngine:
    @staticmethod
    def _apply_common_filters(
        df: pd.DataFrame,
        sector: str | None,
        owner_code: str | None,
        date_col: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> pd.DataFrame:
        out = df.copy()
        if sector:
            out = out[out["sector"].str.lower() == sector.lower()]
        if owner_code and "owner_code" in out.columns:
            out = out[out["owner_code"].fillna("").str.upper() == owner_code.upper()]
        if date_col and start_date and end_date and date_col in out.columns:
            out = out[out[date_col].notna()]
            out = out[(out[date_col] >= start_date) & (out[date_col] <= end_date)]
        return out

    def compute_deals(
        self,
        deals_df: pd.DataFrame,
        sector: str | None,
        owner_code: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> dict:
        if deals_df.empty:
            return {
                "deals_rows": 0,
                "open_pipeline_value": 0.0,
                "weighted_pipeline_value": 0.0,
                "won_value": 0.0,
                "sector_breakdown": [],
                "stage_breakdown": [],
            }

        df = self._apply_common_filters(deals_df, sector, owner_code, "close_date", start_date, end_date)
        open_df = df[df["deal_status"].str.lower() == "open"]
        won_df = df[df["deal_status"].str.lower().isin(["won", "closed won"])]

        sector_breakdown = (
            df.groupby("sector", dropna=False)["deal_value"].sum().sort_values(ascending=False).head(10).to_dict()
        )
        stage_breakdown = (
            df.groupby("deal_stage", dropna=False)["deal_value"].sum().sort_values(ascending=False).head(10).to_dict()
        )

        return {
            "deals_rows": int(len(df)),
            "open_pipeline_value": float(open_df["deal_value"].sum()),
            "weighted_pipeline_value": float(open_df["weighted_value"].sum()),
            "won_value": float(won_df["deal_value"].sum()),
            "sector_breakdown": [{"sector": k, "value": float(v)} for k, v in sector_breakdown.items()],
            "stage_breakdown": [{"stage": k, "value": float(v)} for k, v in stage_breakdown.items()],
        }

    def compute_work_orders(
        self,
        work_orders_df: pd.DataFrame,
        sector: str | None,
        owner_code: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> dict:
        if work_orders_df.empty:
            return {
                "work_order_rows": 0,
                "billed_total": 0.0,
                "collected_total": 0.0,
                "receivable_total": 0.0,
                "collection_efficiency_pct": 0.0,
                "sector_billed_breakdown": [],
            }

        df = self._apply_common_filters(work_orders_df, sector, owner_code, "invoice_date", start_date, end_date)
        billed = float(df["billed_value"].sum())
        collected = float(df["collected_value"].sum())
        receivable = float(df["receivable_value"].sum())
        efficiency = (collected / billed * 100.0) if billed > 0 else 0.0

        sector_breakdown = (
            df.groupby("sector", dropna=False)["billed_value"].sum().sort_values(ascending=False).head(10).to_dict()
        )

        return {
            "work_order_rows": int(len(df)),
            "billed_total": billed,
            "collected_total": collected,
            "receivable_total": receivable,
            "collection_efficiency_pct": round(efficiency, 2),
            "sector_billed_breakdown": [{"sector": k, "value": float(v)} for k, v in sector_breakdown.items()],
        }

    def compute_cross_board_summary(self, deals_metrics: dict, work_metrics: dict) -> dict:
        return {
            "pipeline_to_receivable_ratio": round(
                deals_metrics.get("weighted_pipeline_value", 0.0) / max(work_metrics.get("receivable_total", 1.0), 1.0),
                4,
            ),
            "headline": (
                "Pipeline looks stronger than current receivables exposure"
                if deals_metrics.get("weighted_pipeline_value", 0.0) >= work_metrics.get("receivable_total", 0.0)
                else "Receivables exposure is high relative to weighted pipeline"
            ),
        }
