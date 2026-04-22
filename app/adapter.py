from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import IncomingEvent


class QQLoginAdapter(ABC):
    name: str = "qq_login"

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def send_private_msg(self, user_id: int, message: str | list[dict]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def send_group_msg(self, group_id: int, message: str | list[dict]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def normalize_event(self, payload: dict[str, Any]) -> IncomingEvent:
        raise NotImplementedError


class PlaceholderQQLoginAdapter(QQLoginAdapter):
    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "adapter": self.name,
            "running": self.running,
            "implemented": False,
            "message": "standalone scaffold only",
        }

    async def send_private_msg(self, user_id: int, message: str | list[dict]) -> dict[str, Any]:
        return {"ok": False, "error": "not implemented", "action": "send_private_msg", "user_id": user_id}

    async def send_group_msg(self, group_id: int, message: str | list[dict]) -> dict[str, Any]:
        return {"ok": False, "error": "not implemented", "action": "send_group_msg", "group_id": group_id}

    def normalize_event(self, payload: dict[str, Any]) -> IncomingEvent:
        return IncomingEvent(
            post_type=payload.get("post_type") or "message",
            message_type=payload.get("message_type") or "private",
            user_id=payload.get("user_id"),
            group_id=payload.get("group_id"),
            message_id=payload.get("message_id"),
            raw_message=payload.get("raw_message") or payload.get("text") or "",
            extra={"source": payload.get("source", "standalone")},
        )
