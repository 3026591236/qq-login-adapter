from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import IncomingEvent


def _utcnow() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


class SQLiteStorage:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(
            db_path
            or os.getenv(
                "QQ_LOGIN_ADAPTER_DB_PATH",
                "/root/.openclaw/workspace/qq-login-adapter/data/qq-login-adapter.sqlite3",
            )
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_done = False

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        if not self._init_done:
            self.migrate(conn)
            self._init_done = True
        return conn

    def migrate(self, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS inbound_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              received_at TEXT NOT NULL,
              post_type TEXT NOT NULL,
              message_type TEXT NOT NULL,
              notice_type TEXT NOT NULL,
              request_type TEXT NOT NULL,
              meta_event_type TEXT NOT NULL,
              sub_type TEXT NOT NULL,
              user_id INTEGER,
              group_id INTEGER,
              message_id TEXT,
              raw_message TEXT NOT NULL,
              sender_user_id INTEGER,
              sender_nickname TEXT NOT NULL,
              sender_role TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sent_at TEXT NOT NULL,
              action TEXT NOT NULL,
              target_user_id INTEGER,
              target_group_id INTEGER,
              message_json TEXT NOT NULL,
              response_json TEXT NOT NULL,
              ok INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def save_inbound_event(self, event: IncomingEvent) -> int:
        payload = (event.extra or {}).get("payload")
        payload_json = json.dumps(payload or event.to_framework_like_dict(), ensure_ascii=False)
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO inbound_events (
                  received_at, post_type, message_type, notice_type, request_type, meta_event_type, sub_type,
                  user_id, group_id, message_id, raw_message,
                  sender_user_id, sender_nickname, sender_role,
                  payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.received_at or _utcnow(),
                    event.post_type or "message",
                    event.message_type or "private",
                    event.notice_type or "",
                    event.request_type or "",
                    event.meta_event_type or "",
                    event.sub_type or "",
                    event.user_id,
                    event.group_id,
                    None if event.message_id is None else str(event.message_id),
                    event.raw_message or "",
                    event.sender.user_id,
                    event.sender.nickname or "",
                    event.sender.role or "member",
                    payload_json,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def save_outbound(
        self,
        action: str,
        message: Any,
        response: Any,
        target_user_id: int | None = None,
        target_group_id: int | None = None,
        ok: bool = True,
    ) -> int:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO outbound_messages (
                  sent_at, action, target_user_id, target_group_id, message_json, response_json, ok
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    _utcnow(),
                    action,
                    target_user_id,
                    target_group_id,
                    json.dumps(message, ensure_ascii=False),
                    json.dumps(response, ensure_ascii=False),
                    1 if ok else 0,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def list_inbound_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, received_at, post_type, message_type, notice_type, request_type, meta_event_type, sub_type, user_id, group_id, message_id, raw_message, sender_user_id, sender_nickname, sender_role FROM inbound_events ORDER BY id DESC LIMIT ?",
                (int(limit),),
            )
            return [dict(r) for r in cur.fetchall()]

    def list_outbound(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, sent_at, action, target_user_id, target_group_id, ok FROM outbound_messages ORDER BY id DESC LIMIT ?",
                (int(limit),),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_setting(self, key: str, default: str = "") -> str:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM kv_settings WHERE key=?", (key,))
            row = cur.fetchone()
            return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO kv_settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            conn.commit()
