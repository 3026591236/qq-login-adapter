from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LoginSessionState:
    online: bool = False
    last_login_at: str = ""
    last_offline_at: str = ""
    last_qrcode_at: str = ""
    last_error: str = ""
    metadata: dict = field(default_factory=dict)

    def mark_online(self) -> None:
        self.online = True
        self.last_login_at = datetime.utcnow().isoformat(timespec="seconds")
        self.last_error = ""

    def mark_offline(self, error: str = "") -> None:
        self.online = False
        self.last_offline_at = datetime.utcnow().isoformat(timespec="seconds")
        self.last_error = error

    def mark_qrcode_refresh(self, path: str = "") -> None:
        self.last_qrcode_at = datetime.utcnow().isoformat(timespec="seconds")
        if path:
            self.metadata["qrcode_path"] = path
