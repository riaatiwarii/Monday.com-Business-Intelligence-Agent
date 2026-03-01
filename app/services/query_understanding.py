from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re


@dataclass
class IntentResult:
    metric_focus: str
    boards_required: list[str]
    sector: str | None
    owner_code: str | None
    start_date: datetime | None
    end_date: datetime | None
    clarification_needed: bool
    clarification_question: str | None


class QueryUnderstandingService:
    def parse_intent(self, user_message: str, previous_filters: dict | None = None) -> IntentResult:
        text = user_message.lower().strip()
        previous_filters = previous_filters or {}

        metric_focus = self._detect_metric_focus(text)
        boards = self._detect_boards(text, metric_focus)
        sector = self._extract_sector(text) or previous_filters.get("sector")
        owner_code = self._extract_owner_code(text) or previous_filters.get("owner_code")
        start_date, end_date = self._extract_date_window(text)

        if start_date is None and end_date is None:
            start_date = previous_filters.get("start_date")
            end_date = previous_filters.get("end_date")

        clarification_needed = False
        clarification_question = None
        if metric_focus == "unknown":
            clarification_needed = True
            clarification_question = (
                "Do you want pipeline metrics, work-order billing/collection metrics, or both?"
            )

        return IntentResult(
            metric_focus=metric_focus,
            boards_required=boards,
            sector=sector,
            owner_code=owner_code,
            start_date=start_date,
            end_date=end_date,
            clarification_needed=clarification_needed,
            clarification_question=clarification_question,
        )

    def _detect_metric_focus(self, text: str) -> str:
        if any(k in text for k in ["pipeline", "deal", "funnel", "close", "revenue"]):
            if any(k in text for k in ["work order", "billing", "collection", "receivable"]):
                return "both"
            return "pipeline"
        if any(k in text for k in ["work order", "billing", "collection", "receivable"]):
            return "execution"
        if any(k in text for k in ["sector performance", "overall health", "business health"]):
            return "both"
        return "unknown"

    def _detect_boards(self, text: str, metric_focus: str) -> list[str]:
        if metric_focus == "pipeline":
            return ["deals"]
        if metric_focus == "execution":
            return ["work_orders"]
        if metric_focus == "both":
            return ["deals", "work_orders"]
        if "deal" in text:
            return ["deals"]
        if "work order" in text:
            return ["work_orders"]
        return ["deals", "work_orders"]

    def _extract_sector(self, text: str) -> str | None:
        m = re.search(r"(?:sector|industry)\s+(?:is\s+|for\s+|=\s*)?([a-zA-Z0-9_\-/ ]+)", text)
        if m:
            return m.group(1).strip().title()
        known = ["energy", "mining", "powerline", "solar", "wind", "utilities"]
        for s in known:
            if s in text:
                return s.title()
        return None

    def _extract_owner_code(self, text: str) -> str | None:
        m = re.search(r"owner[_ ]?\d{3}", text, re.IGNORECASE)
        return m.group(0).upper() if m else None

    def _extract_date_window(self, text: str) -> tuple[datetime | None, datetime | None]:
        now = datetime.now(timezone.utc)
        if "this quarter" in text:
            q = (now.month - 1) // 3
            start = datetime(now.year, q * 3 + 1, 1, tzinfo=timezone.utc)
            if q == 3:
                end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            else:
                end = datetime(now.year, q * 3 + 4, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            return start, end
        if "last quarter" in text:
            q = (now.month - 1) // 3
            if q == 0:
                start = datetime(now.year - 1, 10, 1, tzinfo=timezone.utc)
                end = datetime(now.year, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            else:
                start = datetime(now.year, (q - 1) * 3 + 1, 1, tzinfo=timezone.utc)
                end = datetime(now.year, q * 3 + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            return start, end
        if "this month" in text:
            start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            if now.month == 12:
                end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            else:
                end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            return start, end
        if "this year" in text:
            return (
                datetime(now.year, 1, 1, tzinfo=timezone.utc),
                datetime(now.year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1),
            )
        return None, None
