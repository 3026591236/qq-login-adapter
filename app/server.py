from __future__ import annotations

from fastapi import FastAPI, Request

from .adapter import PlaceholderQQLoginAdapter

adapter = PlaceholderQQLoginAdapter()
app = FastAPI(title="qq-login-adapter")


@app.on_event("startup")
async def startup_event() -> None:
    await adapter.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await adapter.stop()


@app.get("/")
async def index() -> dict:
    return {"ok": True, "service": "qq-login-adapter"}


@app.get("/healthz")
async def healthz() -> dict:
    return await adapter.health()


@app.post("/event")
async def ingest_event(request: Request) -> dict:
    payload = await request.json()
    event = adapter.normalize_event(payload)
    return {"ok": True, "normalized": event.to_framework_like_dict()}
