from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


LOGIN_IDLE = "idle"
LOGIN_QRCODE_WAIT_SCAN = "qrcode_wait_scan"
LOGIN_LINK_WAIT_OPEN = "link_wait_open"
LOGIN_PASSWORD_WAIT_RESULT = "password_wait_result"
LOGIN_CAPTCHA_REQUIRED = "captcha_required"
LOGIN_NEW_DEVICE_REQUIRED = "new_device_required"
LOGIN_ONLINE = "online"
LOGIN_OFFLINE = "offline"
LOGIN_ERROR = "error"


@dataclass
class LoginSessionState:
    online: bool = False
    phase: str = LOGIN_IDLE
    login_method: str = ""
    last_login_at: str = ""
    last_offline_at: str = ""
    last_qrcode_at: str = ""
    last_error: str = ""
    account: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def _now(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def begin_qrcode(self, account: str = "", qrcode_path: str = "", login_url: str = "") -> None:
        self.online = False
        self.phase = LOGIN_QRCODE_WAIT_SCAN
        self.login_method = "qrcode"
        self.last_error = ""
        self.account = account or self.account
        self.last_qrcode_at = self._now()
        if qrcode_path:
            self.metadata["qrcode_path"] = qrcode_path
        if login_url:
            self.metadata["login_url"] = login_url

    def begin_link(self, account: str = "", login_url: str = "") -> None:
        self.online = False
        self.phase = LOGIN_LINK_WAIT_OPEN
        self.login_method = "link"
        self.last_error = ""
        self.account = account or self.account
        if login_url:
            self.metadata["login_url"] = login_url

    def begin_password(self, account: str = "") -> None:
        self.online = False
        self.phase = LOGIN_PASSWORD_WAIT_RESULT
        self.login_method = "password"
        self.last_error = ""
        self.account = account or self.account

    def require_captcha(self, captcha_url: str = "", sid: str = "", randstr: str = "") -> None:
        self.online = False
        self.phase = LOGIN_CAPTCHA_REQUIRED
        if captcha_url:
            self.metadata["captcha_url"] = captcha_url
        if sid:
            self.metadata["captcha_sid"] = sid
        if randstr:
            self.metadata["captcha_randstr"] = randstr

    def require_new_device(self, jump_url: str = "", sig: str = "") -> None:
        self.online = False
        self.phase = LOGIN_NEW_DEVICE_REQUIRED
        if jump_url:
            self.metadata["new_device_jump_url"] = jump_url
        if sig:
            self.metadata["new_device_sig"] = sig

    def mark_online(self, account: str = "") -> None:
        self.online = True
        self.phase = LOGIN_ONLINE
        self.last_login_at = self._now()
        self.last_error = ""
        if account:
            self.account = account

    def mark_offline(self, error: str = "") -> None:
        self.online = False
        self.phase = LOGIN_OFFLINE
        self.last_offline_at = self._now()
        self.last_error = error

    def mark_error(self, error: str) -> None:
        self.online = False
        self.phase = LOGIN_ERROR
        self.last_error = error

    def reset(self) -> None:
        account = self.account
        self.__dict__.update(LoginSessionState(account=account).to_dict())
