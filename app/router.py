from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .models import IncomingEvent


@dataclass
class DispatchResult:
    handled: bool
    replies: list[str | list[dict[str, Any]]]
    handler: str = ""


HandlerFunc = Callable[[IncomingEvent], Awaitable[DispatchResult]]


class EventRouter:
    def __init__(self) -> None:
        self._handlers: list[tuple[str, HandlerFunc]] = []

    def register(self, name: str, fn: HandlerFunc) -> None:
        self._handlers.append((name, fn))

    async def dispatch(self, event: IncomingEvent) -> list[DispatchResult]:
        results: list[DispatchResult] = []
        for name, fn in self._handlers:
            try:
                r = await fn(event)
                if r.handler == "":
                    r.handler = name
                results.append(r)
            except Exception as exc:
                results.append(DispatchResult(handled=False, replies=[f"[handler:{name}] error: {exc}"], handler=name))
        return results


def build_default_router() -> EventRouter:
    router = EventRouter()

    async def _ping(event: IncomingEvent) -> DispatchResult:
        if event.post_type != "message":
            return DispatchResult(handled=False, replies=[])
        text = (event.raw_message or "").strip().lower()
        if text in {"ping", "ping?", "机器人ping", "机器人 ping"}:
            return DispatchResult(handled=True, replies=["pong"])
        return DispatchResult(handled=False, replies=[])

    async def _help(event: IncomingEvent) -> DispatchResult:
        if event.post_type != "message":
            return DispatchResult(handled=False, replies=[])
        text = (event.raw_message or "").strip().lower()
        if text not in {"help", "帮助", "菜单"}:
            return DispatchResult(handled=False, replies=[])
        return DispatchResult(
            handled=True,
            replies=[
                "qq-login-adapter 可用命令：\n"
                "- ping\n"
                "- help/帮助\n"
                "说明：这是 login+message 网关层，业务插件可后续接入。"
            ],
        )

    router.register("ping", _ping)
    router.register("help", _help)
    return router
