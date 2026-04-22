from __future__ import annotations

from typing import Any

import httpx


class OneBotClient:
    def __init__(self, base_url: str = "http://127.0.0.1:3000") -> None:
        self.base_url = base_url.rstrip("/")

    async def _post(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.base_url}/{action}", json=payload or {})
            resp.raise_for_status()
            return resp.json()

    async def get_status(self) -> dict[str, Any]:
        return await self._post("get_status")

    async def send_private_msg(self, user_id: int, message: str | list[dict[str, Any]]) -> dict[str, Any]:
        return await self._post("send_private_msg", {"user_id": user_id, "message": message})

    async def send_group_msg(self, group_id: int, message: str | list[dict[str, Any]]) -> dict[str, Any]:
        return await self._post("send_group_msg", {"group_id": group_id, "message": message})
