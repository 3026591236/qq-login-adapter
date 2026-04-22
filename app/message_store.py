from __future__ import annotations

from collections import deque
from typing import Any


class MessageStore:
    def __init__(self, limit: int = 100) -> None:
        self.limit = max(10, int(limit))
        self._recent_events: deque[dict[str, Any]] = deque(maxlen=self.limit)
        self._recent_outbound: deque[dict[str, Any]] = deque(maxlen=self.limit)
        self._stats: dict[str, int] = {
            "message": 0,
            "notice": 0,
            "request": 0,
            "meta_event": 0,
            "other": 0,
            "outbound": 0,
        }

    def add_inbound(self, event: dict[str, Any]) -> None:
        post_type = str(event.get("post_type") or "other")
        if post_type not in self._stats:
            post_type = "other"
        self._stats[post_type] += 1
        self._recent_events.appendleft(event)

    def add_outbound(self, item: dict[str, Any]) -> None:
        self._stats["outbound"] += 1
        self._recent_outbound.appendleft(item)

    def snapshot(self) -> dict[str, Any]:
        return {
            "stats": dict(self._stats),
            "recent_inbound": list(self._recent_events),
            "recent_outbound": list(self._recent_outbound),
        }
