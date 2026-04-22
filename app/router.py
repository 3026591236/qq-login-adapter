from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable

from .models import IncomingEvent


@dataclass
class DispatchResult:
    handled: bool
    replies: list[str | list[dict[str, Any]]]
    handler: str = ""


HandlerFunc = Callable[[IncomingEvent], Awaitable[DispatchResult]]


@dataclass
class HandlerSpec:
    name: str
    fn: HandlerFunc
    priority: int = 0
    post_types: set[str] | None = None


class EventRouter:
    """A tiny plugin router.

    - priority: higher runs first
    - stop_on_handled: by default stops after the first handler that returns handled=True
    - post_types filter: only run for certain event.post_type values
    """

    def __init__(self) -> None:
        self._handlers: list[HandlerSpec] = []

    def register(
        self,
        name: str,
        fn: HandlerFunc,
        *,
        priority: int = 0,
        post_types: Iterable[str] | None = None,
    ) -> None:
        spec = HandlerSpec(
            name=name,
            fn=fn,
            priority=int(priority),
            post_types=set(post_types) if post_types is not None else None,
        )
        self._handlers.append(spec)
        self._handlers.sort(key=lambda s: s.priority, reverse=True)

    def list_handlers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "priority": s.priority,
                "post_types": sorted(list(s.post_types)) if s.post_types else [],
            }
            for s in self._handlers
        ]

    async def dispatch(self, event: IncomingEvent, *, stop_on_handled: bool = True) -> list[DispatchResult]:
        results: list[DispatchResult] = []
        for spec in self._handlers:
            if spec.post_types is not None and event.post_type not in spec.post_types:
                continue
            try:
                r = await spec.fn(event)
                if r.handler == "":
                    r.handler = spec.name
                results.append(r)
                if stop_on_handled and r.handled:
                    break
            except Exception as exc:
                results.append(
                    DispatchResult(
                        handled=False,
                        replies=[f"[handler:{spec.name}] error: {exc}"],
                        handler=spec.name,
                    )
                )
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
                "- echo <文本> (示例插件)\n"
                "说明：这是 login+message 网关层，业务插件可后续接入。"
            ],
        )

    router.register("help", _help, priority=10, post_types=["message"])
    router.register("ping", _ping, priority=20, post_types=["message"])
    return router
