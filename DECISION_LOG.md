# Decision Log (<= 2 pages)

## Objective
Build a founder-facing BI agent that answers natural language questions using live monday.com boards (Deals + Work Orders), while handling messy business data and showing action trace.

## Why this stack
- FastAPI: quick API delivery and easy deployment.
- monday GraphQL API: direct live board access; aligns with assignment's no-cache requirement.
- pandas: resilient normalization and aggregation on messy tabular data.
- Optional OpenAI layer: improves intent interpretation and founder-style narrative output.

## Core architecture
- `/chat/query` handles one conversational turn.
- Intent parsing extracts metric focus, filters, board requirements, and ambiguity.
- Live monday queries execute at runtime every turn.
- Normalization handles nulls, invalid dates, and inconsistent numeric fields.
- BI engine computes pipeline, billing/collection, receivables, and cross-board summaries.
- Trace logger records each major action and is returned in API response.

## Tradeoffs
- In-memory session context is lightweight and simple, but not durable across restarts.
- No persistent store was chosen intentionally to avoid accidental data caching.
- Heuristic intent parser is deterministic and robust; optional LLM can improve nuance.

## Data resilience choices
- Missing closure probability defaults to 0.5 with caveat.
- Invalid dates are excluded from date filters with caveat counts.
- Missing receivable value falls back to `max(billed - collected, 0)`.

## Compliance with assignment constraints
- Live API every query: satisfied.
- No preload/cache: satisfied.
- Handles messy data + caveats: satisfied.
- Clarification and follow-ups: supported.
- Visible action/tool-call trace: supported.

## Future improvements
- Better column mapping bootstrap UI for arbitrary board schemas.
- More advanced time parsing and conversational context grounding.
- Auth and rate limiting for production deployment.
