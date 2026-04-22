from __future__ import annotations

from fastapi import FastAPI, Request
from pydantic import BaseModel

from .adapter import PlaceholderQQLoginAdapter
from .web import render_panel_html

adapter = PlaceholderQQLoginAdapter()
app = FastAPI(title="qq-login-adapter")


class LoginStartRequest(BaseModel):
    account: str = ""


class PasswordLoginRequest(BaseModel):
    account: str
    password: str


class CaptchaSubmitRequest(BaseModel):
    ticket: str
    randstr: str = ""
    sid: str = ""


class NewDeviceConfirmRequest(BaseModel):
    confirm_token: str


class NewDeviceQRCodeRequest(BaseModel):
    jump_url: str = ""


class NewDevicePollRequest(BaseModel):
    bytes_token: str


class WatchdogStartRequest(BaseModel):
    interval_seconds: int = 30


class SendPrivateMessageRequest(BaseModel):
    user_id: int
    message: str


class SendGroupMessageRequest(BaseModel):
    group_id: int
    message: str


class LogoutRequest(BaseModel):
    reason: str = "manual logout"


@app.on_event("startup")
async def startup_event() -> None:
    await adapter.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await adapter.stop()


@app.get("/")
async def index() -> dict:
    return {"ok": True, "service": "qq-login-adapter"}


@app.get("/panel")
async def panel():
    return render_panel_html()


@app.get("/healthz")
async def healthz() -> dict:
    return await adapter.health()


@app.get("/login/state")
async def login_state() -> dict:
    return await adapter.get_login_state()


@app.post("/login/qrcode")
async def login_qrcode(body: LoginStartRequest) -> dict:
    return await adapter.begin_qrcode_login(account=body.account)


@app.post("/login/link")
async def login_link(body: LoginStartRequest) -> dict:
    return await adapter.begin_link_login(account=body.account)


@app.post("/login/password")
async def login_password(body: PasswordLoginRequest) -> dict:
    return await adapter.begin_password_login(account=body.account, password=body.password)


@app.post("/login/qrcode/scanned")
async def login_qrcode_scanned() -> dict:
    return await adapter.mark_qrcode_scanned()


@app.post("/login/captcha")
async def login_captcha(body: CaptchaSubmitRequest) -> dict:
    return await adapter.submit_captcha(ticket=body.ticket, randstr=body.randstr, sid=body.sid)


@app.post("/login/new-device")
async def login_new_device(body: NewDeviceConfirmRequest) -> dict:
    return await adapter.complete_new_device_verification(confirm_token=body.confirm_token)


@app.post("/login/new-device/qrcode")
async def login_new_device_qrcode(body: NewDeviceQRCodeRequest) -> dict:
    return await adapter.get_new_device_qrcode(jump_url=body.jump_url)


@app.post("/login/new-device/poll")
async def login_new_device_poll(body: NewDevicePollRequest) -> dict:
    return await adapter.poll_new_device_qr(bytes_token=body.bytes_token)


@app.get("/login/qrcode/export")
async def login_qrcode_export() -> dict:
    return await adapter.export_qrcode_image()


@app.post("/watchdog/check")
async def watchdog_check() -> dict:
    return await adapter.watchdog_check_once()


@app.post("/watchdog/start")
async def watchdog_start(body: WatchdogStartRequest) -> dict:
    return await adapter.watchdog_start(interval_seconds=body.interval_seconds)


@app.post("/watchdog/stop")
async def watchdog_stop() -> dict:
    return await adapter.watchdog_stop()


@app.get("/watchdog/status")
async def watchdog_status() -> dict:
    return await adapter.watchdog_status()


@app.post("/message/private")
async def send_private_message(body: SendPrivateMessageRequest) -> dict:
    return await adapter.send_private_msg(user_id=body.user_id, message=body.message)


@app.post("/message/group")
async def send_group_message(body: SendGroupMessageRequest) -> dict:
    return await adapter.send_group_msg(group_id=body.group_id, message=body.message)


@app.get("/messages")
async def message_snapshot() -> dict:
    return await adapter.get_message_snapshot()


@app.post("/login/logout")
async def login_logout(body: LogoutRequest) -> dict:
    return await adapter.logout(reason=body.reason)


@app.post("/event")
async def ingest_event(request: Request) -> dict:
    payload = await request.json()
    event = adapter.normalize_event(payload)
    return {"ok": True, "normalized": event.to_framework_like_dict()}
