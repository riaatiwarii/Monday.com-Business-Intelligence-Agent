from __future__ import annotations

from datetime import datetime

from app.config import settings


class ResponseGenerator:
    def __init__(self) -> None:
        self._client = None
        if settings.openai_api_key:
            try:
                from openai import OpenAI  # type: ignore
            except Exception:  # noqa: BLE001
                self._client = None
            else:
                self._client = OpenAI(api_key=settings.openai_api_key)

    def generate(
        self,
        user_message: str,
        insights: dict,
        caveats: list[str],
        trace: list[str],
        fetched_at_utc: datetime,
    ) -> str:
        if not self._client:
            return self._template_answer(user_message, insights, caveats, fetched_at_utc)

        prompt = (
            "You are a founder-facing BI analyst. Provide concise, actionable summary with numbers. "
            "Mention caveats clearly.\n"
            f"User question: {user_message}\n"
            f"Insights: {insights}\n"
            f"Caveats: {caveats}\n"
            f"Trace: {trace}\n"
            f"Fetched at UTC: {fetched_at_utc.isoformat()}"
        )
        response = self._client.responses.create(
            model=settings.openai_model,
            input=prompt,
            temperature=0.2,
        )
        return (response.output_text or "").strip() or self._template_answer(
            user_message, insights, caveats, fetched_at_utc
        )

    def _template_answer(
        self,
        user_message: str,
        insights: dict,
        caveats: list[str],
        fetched_at_utc: datetime,
    ) -> str:
        deals = insights.get("deals", {})
        work = insights.get("work_orders", {})
        cross = insights.get("cross_board", {})
        lines = [
            f"For: '{user_message}', I fetched live monday.com data at {fetched_at_utc.isoformat()}.",
            f"Open pipeline: {deals.get('open_pipeline_value', 0):,.2f}; weighted pipeline: {deals.get('weighted_pipeline_value', 0):,.2f}.",
            f"Billed: {work.get('billed_total', 0):,.2f}; collected: {work.get('collected_total', 0):,.2f}; receivable: {work.get('receivable_total', 0):,.2f}.",
            f"Cross-board signal: {cross.get('headline', 'No cross-board conclusion available.')}",
        ]
        if caveats:
            lines.append("Data caveats: " + " | ".join(caveats))
        return "\n".join(lines)
