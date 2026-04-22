from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Any

from .message_store import MessageStore
from .models import IncomingEvent, SenderInfo
from .napcat_client import NapCatWebUIClient
from .onebot_client import OneBotClient
from .qrcode_utils import export_napcat_qrcode
from .session import LoginSessionState
from .watchdog import LoginWatchdog


class QQLoginAdapter(ABC):
    name: str = "qq_login"

    @abstractmethod
    async def sync_login_state(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def export_qrcode_image(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def watchdog_check_once(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def watchdog_start(self, interval_seconds: int = 30) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def watchdog_stop(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def watchdog_status(self) -> dict[str, Any]:
        raise NotImplementedError

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
    async def get_login_state(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def begin_qrcode_login(self, account: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def begin_link_login(self, account: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def begin_password_login(self, account: str, password: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def submit_captcha(self, ticket: str, randstr: str = "", sid: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def complete_new_device_verification(self, confirm_token: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_new_device_qrcode(self, jump_url: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def poll_new_device_qr(self, bytes_token: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def mark_qrcode_scanned(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def logout(self, reason: str = "manual logout") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def send_private_msg(self, user_id: int, message: str | list[dict]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def send_group_msg(self, group_id: int, message: str | list[dict]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_message_snapshot(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def normalize_event(self, payload: dict[str, Any]) -> IncomingEvent:
        raise NotImplementedError


class PlaceholderQQLoginAdapter(QQLoginAdapter):
    def __init__(self) -> None:
        self.running = False
        self.state = LoginSessionState()
        self.client = NapCatWebUIClient()
        self.onebot = OneBotClient()
        self.store = MessageStore(limit=200)
        self.watchdog = LoginWatchdog(self.client)
        self._not_ready_message = "已接入登录管理与基础消息收发，完整独立协议层仍未完成"
        self._password_md5 = ""

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False
        await self.watchdog.stop()

    async def sync_login_state(self) -> dict[str, Any]:
        info_resp = await self.client.get_login_info()
        napcat_info = ((info_resp or {}).get("data") or {}) if isinstance(info_resp, dict) else {}
        online = bool(napcat_info.get("online"))
        if online:
            self.state.mark_online(account=str(napcat_info.get("uin") or self.state.account or ""))
            self.state.metadata["nick"] = str(napcat_info.get("nick") or "")
            self.state.metadata["uid"] = str(napcat_info.get("uid") or "")
        elif self.state.phase == "online":
            self.state.mark_offline("napcat reports offline")
        return napcat_info

    async def export_qrcode_image(self) -> dict[str, Any]:
        result = export_napcat_qrcode()
        self.state.metadata["qrcode_path"] = result["path"]
        return {"ok": True, "message": "二维码已导出", "data": result, "state": self.state.to_dict()}

    async def watchdog_check_once(self) -> dict[str, Any]:
        return await self.watchdog.check_once()

    async def watchdog_start(self, interval_seconds: int = 30) -> dict[str, Any]:
        return await self.watchdog.start(interval_seconds=interval_seconds)

    async def watchdog_stop(self) -> dict[str, Any]:
        return await self.watchdog.stop()

    async def watchdog_status(self) -> dict[str, Any]:
        return await self.watchdog.status()

    async def health(self) -> dict[str, Any]:
        napcat_ok = True
        napcat_info: dict[str, Any] = {}
        try:
            napcat_info = await self.sync_login_state()
        except Exception as exc:
            napcat_ok = False
            self.state.mark_error(f"NapCat WebUI unavailable: {exc}")
        onebot_ok = True
        onebot_info: dict[str, Any] = {}
        try:
            onebot_resp = await self.onebot.get_status()
            onebot_info = ((onebot_resp or {}).get("data") or {}) if isinstance(onebot_resp, dict) else {}
        except Exception as exc:
            onebot_ok = False
            onebot_info = {"error": str(exc)}
        return {
            "ok": True,
            "adapter": self.name,
            "running": self.running,
            "implemented": False,
            "message": self._not_ready_message,
            "napcat_ok": napcat_ok,
            "napcat_info": napcat_info,
            "onebot_ok": onebot_ok,
            "onebot_info": onebot_info,
            "watchdog": (await self.watchdog.status())["state"],
            "login_state": self.state.to_dict(),
            "messages": self.store.snapshot(),
        }

    async def get_login_state(self) -> dict[str, Any]:
        try:
            napcat_info = await self.sync_login_state()
        except Exception as exc:
            napcat_info = {"error": str(exc)}
        return {"ok": True, "state": self.state.to_dict(), "napcat_info": napcat_info}

    async def begin_qrcode_login(self, account: str = "") -> dict[str, Any]:
        await self.client.refresh_qrcode()
        qrcode_resp = await self.client.get_qrcode()
        data = ((qrcode_resp or {}).get("data") or {}) if isinstance(qrcode_resp, dict) else {}
        qrcode_url = str(data.get("qrcode") or "")
        export_info = None
        qrcode_path = "/root/.openclaw/workspace/qq-login-adapter/runtime/qrcode.png"
        try:
            export_info = export_napcat_qrcode()
            qrcode_path = str(export_info["path"])
        except Exception:
            pass
        self.state.begin_qrcode(account=account, qrcode_path=qrcode_path, login_url=qrcode_url)
        return {
            "ok": True,
            "message": "已进入扫码登录流程（真实调用 NapCat）",
            "qrcode_url": qrcode_url,
            "qrcode_path": qrcode_path,
            "qrcode_export": export_info,
            "state": self.state.to_dict(),
            "next_action": "scan_qrcode",
        }

    async def begin_link_login(self, account: str = "") -> dict[str, Any]:
        await self.client.refresh_qrcode()
        qrcode_resp = await self.client.get_qrcode()
        data = ((qrcode_resp or {}).get("data") or {}) if isinstance(qrcode_resp, dict) else {}
        login_url = str(data.get("qrcode") or "")
        self.state.begin_link(account=account, login_url=login_url)
        return {
            "ok": True,
            "message": "已进入链接登录流程（真实调用 NapCat）",
            "state": self.state.to_dict(),
            "next_action": "open_login_link",
        }

    async def begin_password_login(self, account: str, password: str) -> dict[str, Any]:
        if not account:
            return {"ok": False, "error": "account is required"}
        if not password:
            return {"ok": False, "error": "password is required"}
        self.state.begin_password(account=account)
        self._password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        resp = await self.client.password_login(account, self._password_md5)
        data = ((resp or {}).get("data") or {}) if isinstance(resp, dict) else {}
        code = (resp or {}).get("code") if isinstance(resp, dict) else None
        if code == 0 and not data:
            self.state.mark_online(account=account)
            return {
                "ok": True,
                "message": "密码登录成功（真实调用 NapCat）",
                "password_supported": True,
                "state": self.state.to_dict(),
            }
        if data.get("needCaptcha"):
            self.state.require_captcha(captcha_url=str(data.get("proofWaterUrl") or ""))
            return {
                "ok": True,
                "message": "密码登录需要验证码，请人工辅助",
                "password_supported": True,
                "state": self.state.to_dict(),
                "next_action": "submit_captcha",
            }
        if data.get("needNewDevice"):
            self.state.require_new_device(
                jump_url=str(data.get("jumpUrl") or ""),
                sig=str(data.get("newDevicePullQrCodeSig") or ""),
            )
            return {
                "ok": True,
                "message": "密码登录需要新设备确认，请人工辅助",
                "password_supported": True,
                "state": self.state.to_dict(),
                "next_action": "complete_new_device_verification",
            }
        self.state.mark_error(str((resp or {}).get("message") or "password login failed"))
        return {"ok": False, "error": self.state.last_error, "state": self.state.to_dict()}

    async def submit_captcha(self, ticket: str, randstr: str = "", sid: str = "") -> dict[str, Any]:
        if self.state.phase != "captcha_required":
            return {"ok": False, "error": "captcha is not required in current phase", "state": self.state.to_dict()}
        if not ticket:
            return {"ok": False, "error": "ticket is required", "state": self.state.to_dict()}
        if not self._password_md5:
            return {"ok": False, "error": "password login context missing", "state": self.state.to_dict()}
        resp = await self.client.captcha_login(self.state.account, self._password_md5, ticket, randstr, sid)
        data = ((resp or {}).get("data") or {}) if isinstance(resp, dict) else {}
        code = (resp or {}).get("code") if isinstance(resp, dict) else None
        if code == 0 and not data:
            self.state.mark_online(account=self.state.account)
            return {
                "ok": True,
                "message": "验证码已提交，登录成功（真实调用 NapCat）",
                "state": self.state.to_dict(),
            }
        if data.get("needNewDevice"):
            self.state.require_new_device(
                jump_url=str(data.get("jumpUrl") or ""),
                sig=str(data.get("newDevicePullQrCodeSig") or ""),
            )
            return {
                "ok": True,
                "message": "验证码已提交，当前需要新设备确认",
                "state": self.state.to_dict(),
                "next_action": "complete_new_device_verification",
            }
        self.state.mark_error(str((resp or {}).get("message") or "captcha login failed"))
        return {"ok": False, "error": self.state.last_error, "state": self.state.to_dict()}

    async def complete_new_device_verification(self, confirm_token: str = "") -> dict[str, Any]:
        if self.state.phase != "new_device_required":
            return {"ok": False, "error": "new device verification is not required", "state": self.state.to_dict()}
        sig = str(self.state.metadata.get("new_device_sig") or confirm_token or "")
        if not sig:
            return {"ok": False, "error": "confirm_token is required", "state": self.state.to_dict()}
        if not self._password_md5:
            return {"ok": False, "error": "password login context missing", "state": self.state.to_dict()}
        resp = await self.client.new_device_login(self.state.account, self._password_md5, sig)
        data = ((resp or {}).get("data") or {}) if isinstance(resp, dict) else {}
        code = (resp or {}).get("code") if isinstance(resp, dict) else None
        if code == 0 and not data:
            self.state.mark_online(account=self.state.account)
            return {
                "ok": True,
                "message": "新设备确认已完成，登录成功（真实调用 NapCat）",
                "state": self.state.to_dict(),
            }
        if data.get("needNewDevice"):
            self.state.require_new_device(
                jump_url=str(data.get("jumpUrl") or ""),
                sig=str(data.get("newDevicePullQrCodeSig") or ""),
            )
            return {
                "ok": True,
                "message": "仍需继续新设备确认，请人工辅助",
                "state": self.state.to_dict(),
                "next_action": "complete_new_device_verification",
            }
        self.state.mark_error(str((resp or {}).get("message") or "new device login failed"))
        return {"ok": False, "error": self.state.last_error, "state": self.state.to_dict()}

    async def get_new_device_qrcode(self, jump_url: str = "") -> dict[str, Any]:
        if self.state.phase != "new_device_required":
            return {"ok": False, "error": "new device verification is not required", "state": self.state.to_dict()}
        final_jump_url = jump_url or str(self.state.metadata.get("new_device_jump_url") or "")
        if not final_jump_url:
            return {"ok": False, "error": "jump_url is required", "state": self.state.to_dict()}
        resp = await self.client.get_new_device_qrcode(self.state.account, final_jump_url)
        data = ((resp or {}).get("data") or {}) if isinstance(resp, dict) else {}
        if data:
            self.state.metadata["new_device_qr"] = data
        return {"ok": True, "message": "已获取新设备确认二维码", "data": data, "state": self.state.to_dict()}

    async def poll_new_device_qr(self, bytes_token: str) -> dict[str, Any]:
        if not bytes_token:
            return {"ok": False, "error": "bytes_token is required", "state": self.state.to_dict()}
        resp = await self.client.poll_new_device_qr(self.state.account, bytes_token)
        data = ((resp or {}).get("data") or {}) if isinstance(resp, dict) else {}
        return {"ok": True, "message": "已轮询新设备二维码状态", "data": data, "state": self.state.to_dict()}

    async def mark_qrcode_scanned(self) -> dict[str, Any]:
        if self.state.phase not in {"qrcode_wait_scan", "link_wait_open"}:
            return {"ok": False, "error": "current phase is not waiting for qrcode/link confirmation", "state": self.state.to_dict()}
        info_resp = await self.client.get_login_info()
        data = ((info_resp or {}).get("data") or {}) if isinstance(info_resp, dict) else {}
        if data.get("online"):
            self.state.mark_online(account=str(data.get("uin") or self.state.account or ""))
            return {
                "ok": True,
                "message": "扫码/链接登录已完成（真实读取 NapCat 状态）",
                "state": self.state.to_dict(),
            }
        return {
            "ok": False,
            "error": "NapCat 仍未显示在线，请完成扫码/确认后再试",
            "state": self.state.to_dict(),
        }

    async def logout(self, reason: str = "manual logout") -> dict[str, Any]:
        self.state.mark_offline(reason)
        return {"ok": True, "message": "已退出当前登录态", "state": self.state.to_dict()}

    async def send_private_msg(self, user_id: int, message: str | list[dict]) -> dict[str, Any]:
        resp = await self.onebot.send_private_msg(user_id, message)
        self.store.add_outbound({
            "action": "send_private_msg",
            "user_id": int(user_id),
            "message": message,
            "response": resp,
        })
        return {"ok": True, "action": "send_private_msg", "response": resp, "state": self.state.to_dict()}

    async def send_group_msg(self, group_id: int, message: str | list[dict]) -> dict[str, Any]:
        resp = await self.onebot.send_group_msg(group_id, message)
        self.store.add_outbound({
            "action": "send_group_msg",
            "group_id": int(group_id),
            "message": message,
            "response": resp,
        })
        return {"ok": True, "action": "send_group_msg", "response": resp, "state": self.state.to_dict()}

    async def get_message_snapshot(self) -> dict[str, Any]:
        return {"ok": True, **self.store.snapshot()}

    def normalize_event(self, payload: dict[str, Any]) -> IncomingEvent:
        sender = payload.get("sender") or {}
        message = payload.get("message") if isinstance(payload.get("message"), list) else []
        event = IncomingEvent(
            post_type=payload.get("post_type") or "message",
            message_type=payload.get("message_type") or "private",
            notice_type=payload.get("notice_type") or "",
            request_type=payload.get("request_type") or "",
            meta_event_type=payload.get("meta_event_type") or "",
            sub_type=payload.get("sub_type") or "",
            user_id=payload.get("user_id"),
            group_id=payload.get("group_id"),
            message_id=payload.get("message_id"),
            raw_message=payload.get("raw_message") or payload.get("text") or "",
            sender=SenderInfo(
                user_id=sender.get("user_id") or payload.get("user_id"),
                nickname=str(sender.get("nickname") or sender.get("card") or ""),
                role=str(sender.get("role") or "member"),
            ),
            message=message,
            extra={"source": payload.get("source", "onebot"), "payload": payload},
        )
        self.store.add_inbound(event.to_framework_like_dict())
        return event
