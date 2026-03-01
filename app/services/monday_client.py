from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import httpx

from app.config import settings


class MondayClient:
    def __init__(self) -> None:
        if not settings.monday_api_token:
            raise RuntimeError("MONDAY_API_TOKEN is missing.")
        self._url = settings.monday_api_url
        self._headers = {
            "Authorization": settings.monday_api_token,
            "Content-Type": "application/json",
            "API-Version": settings.monday_api_version,
        }

    async def _graphql(self, query: str, variables: dict | None = None) -> dict:
        payload = {"query": query, "variables": variables or {}}
        timeout = httpx.Timeout(30.0)

        last_error: Exception | None = None
        for _ in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(self._url, headers=self._headers, json=payload)
                response.raise_for_status()
                data = response.json()
                if "errors" in data and data["errors"]:
                    raise RuntimeError(str(data["errors"]))
                return data["data"]
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                await asyncio.sleep(0.6)

        raise RuntimeError(f"Monday API request failed after retries: {last_error}")

    async def _fetch_board_columns(self, board_id: int) -> list[dict]:
        query = """
        query($board_id: [ID!]) {
          boards(ids: $board_id) {
            id
            columns {
              id
              title
              type
            }
          }
        }
        """
        data = await self._graphql(query, {"board_id": str(board_id)})
        boards = data.get("boards", [])
        if not boards:
            return []
        return boards[0].get("columns", [])

    async def fetch_runtime_context(self) -> dict:
        if settings.monday_deals_board_id is None:
            raise RuntimeError("MONDAY_DEALS_BOARD_ID is missing.")
        if settings.monday_work_orders_board_id is None:
            raise RuntimeError("MONDAY_WORK_ORDERS_BOARD_ID is missing.")

        query = """
        query($board_ids: [ID!]) {
          boards(ids: $board_ids) {
            id
            name
            state
            items_page(limit: 1) {
              items {
                id
              }
            }
          }
        }
        """
        data = await self._graphql(
            query,
            {
                "board_ids": [
                    str(settings.monday_deals_board_id),
                    str(settings.monday_work_orders_board_id),
                ]
            },
        )
        boards = data.get("boards", [])
        return {
            "board_count": len(boards),
            "boards": [
                {
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "state": b.get("state"),
                }
                for b in boards
            ],
        }

    async def _iterate_board_items(self, board_id: int) -> AsyncIterator[list[dict]]:
        cursor = None
        while True:
            query = """
            query($board_id: [ID!], $cursor: String) {
              boards(ids: $board_id) {
                items_page(limit: 200, cursor: $cursor) {
                  cursor
                  items {
                    id
                    name
                    group {
                      title
                    }
                    column_values {
                      id
                      text
                    }
                  }
                }
              }
            }
            """
            data = await self._graphql(
                query,
                {"board_id": str(board_id), "cursor": cursor},
            )
            boards = data.get("boards", [])
            if not boards:
                break
            page = boards[0].get("items_page", {})
            items = page.get("items", [])
            if not items:
                break
            yield items
            cursor = page.get("cursor")
            if not cursor:
                break

    async def fetch_board_records(self, board_id: int) -> list[dict]:
        columns = await self._fetch_board_columns(board_id)
        title_by_id = {c["id"]: c["title"] for c in columns}

        out: list[dict] = []
        async for batch in self._iterate_board_items(board_id):
            for item in batch:
                values_by_id = {cv.get("id"): cv.get("text") for cv in item.get("column_values", [])}
                values_by_title = {
                    title_by_id.get(col_id, col_id): value
                    for col_id, value in values_by_id.items()
                }
                out.append(
                    {
                        "item_id": item.get("id"),
                        "item_name": item.get("name"),
                        "group": (item.get("group") or {}).get("title"),
                        "values_by_id": values_by_id,
                        "values_by_title": values_by_title,
                    }
                )
        return out

    async def fetch_deals(self) -> list[dict]:
        if settings.monday_deals_board_id is None:
            raise RuntimeError("MONDAY_DEALS_BOARD_ID is missing.")
        return await self.fetch_board_records(settings.monday_deals_board_id)

    async def fetch_work_orders(self) -> list[dict]:
        if settings.monday_work_orders_board_id is None:
            raise RuntimeError("MONDAY_WORK_ORDERS_BOARD_ID is missing.")
        return await self.fetch_board_records(settings.monday_work_orders_board_id)
