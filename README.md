# Monday BI Agent

Founder-level BI conversational agent using live monday.com board data.

## What this project guarantees
- Live monday GraphQL API calls on every query.
- No preload or caching of monday board data.
- Handles messy/null fields with normalization and caveats.
- Clarifying questions when intent is ambiguous.
- Action visibility via explicit per-request trace.

## PDF Requirement Mapping
- Monday.com Integration (Live): Implemented via GraphQL calls in each `/chat/query` run, including a mandatory runtime-context call plus board data calls.
- Data Resilience: Missing/null values, inconsistent numbers/dates, and fallback probability handling with explicit caveat messages.
- Query Understanding: Intent parsing + clarification prompt when ambiguous + follow-up filters via `session_id`.
- Business Intelligence: Pipeline, weighted pipeline, billing/collection/receivable metrics, and cross-board summary.
- Agent Action Visibility: `trace` field includes live API call steps and processing steps.

## Stack
- FastAPI
- monday GraphQL API
- pandas
- OpenAI API (optional but recommended for response quality)
- pytest

## Setup
1. Create and activate a virtual env.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values.

Required `.env` values:
- `MONDAY_API_TOKEN`
- `MONDAY_DEALS_BOARD_ID`
- `MONDAY_WORK_ORDERS_BOARD_ID`

Optional:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

## Run
`uvicorn app.main:app --reload --port 8000`

## API
- `GET /health`
- `POST /chat/query`
- `POST /chat/reset`

### Example query payload
```json
{
  "session_id": "founder-1",
  "user_message": "How is our pipeline for the energy sector this quarter?"
}
```

### Example response fields
- `answer`
- `clarification_needed`
- `clarification_question`
- `insights`
- `data_quality_caveats`
- `trace`
- `fetched_at_utc`

## monday board mapping notes
The normalizer reads monday column titles from imported board columns. Keep column titles close to the source file names for best accuracy.

Deals board expected titles include:
- `Deal Status`
- `Closure Probability`
- `Masked Deal value`
- `Tentative Close Date` or `Close Date (A)`
- `Deal Stage`
- `Sector/service`

Work Orders expected titles include:
- `Billed Value in Rupees (Incl of GST.) (Masked)`
- `Collected Amount in Rupees (Incl of GST.) (Masked)`
- `Amount Receivable (Masked)`
- `WO Status (billed)` or `Execution Status`
- `Sector`

## Testing
`pytest -q`

## Demo checklist (for evaluator)
1. Ask a pipeline-only question.
2. Ask a work-order collections question.
3. Ask a cross-board sector question.
4. Ask an ambiguous question and verify clarification.
5. Confirm response includes live trace entries.
6. Confirm `trace` starts with `monday_api_called: runtime_context ...` for every query.
