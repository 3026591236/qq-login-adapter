from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SenderInfo:
    user_id: int | None = None
    nickname: str = ""
    role: str = "member"


@dataclass
class IncomingEvent:
    post_type: str = "message"
    message_type: str = "private"
    user_id: int | None = None
    group_id: int | None = None
    message_id: int | str | None = None
    raw_message: str = ""
    sender: SenderInfo = field(default_factory=SenderInfo)
    message: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_framework_like_dict(self) -> dict[str, Any]:
        return {
            "post_type": self.post_type,
            "message_type": self.message_type,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "message_id": self.message_id,
            "raw_message": self.raw_message,
            "sender": {
                "user_id": self.sender.user_id,
                "nickname": self.sender.nickname,
                "role": self.sender.role,
            },
            "message": self.message,
            **self.extra,
        }
