from __future__ import annotations

import asyncio
from typing import Any

from .napcat_client import NapCatWebUIClient
from .qrcode_utils import export_napcat_qrcode


class LoginWatchdog:
    def __init__(self, client: NapCatWebUIClient) -> None:
        self.client = client
        self.running = False
        self.task: asyncio.Task | None = None
        self.last_result: dict[str, Any] = {
            "running": False,
            "last_check": None,
            "last_status": "idle",
            "last_error": "",
            "last_qrcode_export": None,
        }

    async def check_once(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "running": self.running,
            "last_status": "ok",
            "last_error": "",
            "napcat_info": {},
            "qrcode_export": None,
        }
        try:
            info_resp = await self.client.get_login_info()
            info = ((info_resp or {}).get("data") or {}) if isinstance(info_resp, dict) else {}
            result["napcat_info"] = info
            if not info.get("online"):
                await self.client.refresh_qrcode()
                try:
                    result["qrcode_export"] = export_napcat_qrcode()
                except Exception as exc:
                    result["last_status"] = "degraded"
                    result["last_error"] = f"qrcode export failed: {exc}"
        except Exception as exc:
            result["last_status"] = "error"
            result["last_error"] = str(exc)
        self.last_result = result
        return result

    async def _loop(self, interval_seconds: int) -> None:
        while self.running:
            await self.check_once()
            await asyncio.sleep(interval_seconds)

    async def start(self, interval_seconds: int = 30) -> dict[str, Any]:
        if self.running:
            return {"ok": True, "message": "watchdog already running", "state": self.last_result}
        self.running = True
        self.last_result["running"] = True
        self.task = asyncio.create_task(self._loop(interval_seconds))
        return {"ok": True, "message": "watchdog started", "interval_seconds": interval_seconds}

    async def stop(self) -> dict[str, Any]:
        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None
        self.last_result["running"] = False
        return {"ok": True, "message": "watchdog stopped", "state": self.last_result}

    async def status(self) -> dict[str, Any]:
        return {"ok": True, "state": self.last_result}
