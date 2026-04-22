from __future__ import annotations

from app.models import IncomingEvent
from app.router import DispatchResult, EventRouter


def register(router: EventRouter) -> None:
    async def _echo(event: IncomingEvent) -> DispatchResult:
        if event.post_type != "message":
            return DispatchResult(handled=False, replies=[])
        text = (event.raw_message or "").strip()
        if not text.startswith("echo "):
            return DispatchResult(handled=False, replies=[])
        return DispatchResult(handled=True, replies=[text[len("echo ") :]])

    router.register("echo", _echo)
