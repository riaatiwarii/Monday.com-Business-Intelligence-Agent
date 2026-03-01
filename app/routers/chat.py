from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.memory.session_store import session_store
from app.models import QueryRequest, QueryResponse, ResetRequest
from app.services.bi_engine import BIEngine
from app.services.data_normalizer import normalize_deals, normalize_work_orders
from app.services.monday_client import MondayClient
from app.services.query_understanding import QueryUnderstandingService
from app.services.response_generator import ResponseGenerator
from app.services.trace_logger import TraceLogger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/reset")
async def reset_session(request: ResetRequest) -> dict:
    session_store.clear(request.session_id)
    return {"status": "ok", "session_id": request.session_id}


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    trace = TraceLogger()
    trace.add("received_user_query")
    fetched_at_utc = datetime.now(timezone.utc)

    # Assignment compliance: every query performs live monday API calls at runtime.
    try:
        monday = MondayClient()
        runtime_context = await monday.fetch_runtime_context()
        trace.add(
            "monday_api_called: runtime_context "
            f"board_count={runtime_context.get('board_count', 0)}"
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Live monday API call failed: {exc}")

    previous = session_store.get(request.session_id)
    parser = QueryUnderstandingService()
    intent = parser.parse_intent(request.user_message, previous_filters=previous.get("filters") if previous else None)
    trace.add("intent_parsed")

    if intent.clarification_needed:
        trace.add("clarification_requested")
        return QueryResponse(
            answer="Need one clarification before I run live board queries.",
            clarification_needed=True,
            clarification_question=intent.clarification_question,
            insights={},
            data_quality_caveats=[],
            trace=trace.steps,
            fetched_at_utc=fetched_at_utc.isoformat(),
        )

    deals_raw: list[dict] = []
    work_orders_raw: list[dict] = []

    try:
        if "deals" in intent.boards_required:
            deals_raw = await monday.fetch_deals()
            trace.add(f"monday_api_called: deals_board rows={len(deals_raw)}")

        if "work_orders" in intent.boards_required:
            work_orders_raw = await monday.fetch_work_orders()
            trace.add(f"monday_api_called: work_orders_board rows={len(work_orders_raw)}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Live monday API call failed: {exc}")

    caveats: list[str] = []
    deals_df, deals_caveats = normalize_deals(deals_raw) if deals_raw else (None, [])
    work_df, work_caveats = normalize_work_orders(work_orders_raw) if work_orders_raw else (None, [])
    caveats.extend(deals_caveats)
    caveats.extend(work_caveats)
    trace.add("normalization_completed")

    engine = BIEngine()
    deals_metrics = (
        engine.compute_deals(deals_df, intent.sector, intent.owner_code, intent.start_date, intent.end_date)
        if deals_df is not None
        else {}
    )
    work_metrics = (
        engine.compute_work_orders(work_df, intent.sector, intent.owner_code, intent.start_date, intent.end_date)
        if work_df is not None
        else {}
    )
    cross_metrics = engine.compute_cross_board_summary(deals_metrics, work_metrics)
    trace.add("bi_metrics_computed")

    insights = {
        "filters": {
            "sector": intent.sector,
            "owner_code": intent.owner_code,
            "start_date": intent.start_date.isoformat() if intent.start_date else None,
            "end_date": intent.end_date.isoformat() if intent.end_date else None,
        },
        "deals": deals_metrics,
        "work_orders": work_metrics,
        "cross_board": cross_metrics,
    }

    generator = ResponseGenerator()
    answer = generator.generate(request.user_message, insights, caveats, trace.steps, fetched_at_utc)
    trace.add("response_generated")

    session_store.set(
        request.session_id,
        {
            "last_question": request.user_message,
            "filters": {
                "sector": intent.sector,
                "owner_code": intent.owner_code,
                "start_date": intent.start_date,
                "end_date": intent.end_date,
            },
        },
    )

    return QueryResponse(
        answer=answer,
        clarification_needed=False,
        clarification_question=None,
        insights=insights,
        data_quality_caveats=caveats,
        trace=trace.steps,
        fetched_at_utc=fetched_at_utc.isoformat(),
    )
