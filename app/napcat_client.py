from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx


class NapCatWebUIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:6099", config_path: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.config_path = Path(config_path or "/root/.openclaw/workspace/qqbot-framework/napcat/config/webui.json")
        self._credential: str = ""
        self._token: str = ""

    def _load_token(self) -> str:
        if self._token:
            return self._token
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        token = str(data.get("token") or "").strip()
        if not token:
            raise RuntimeError(f"webui token missing in {self.config_path}")
        self._token = token
        return token

    def _token_hash(self) -> str:
        token = self._load_token()
        return hashlib.sha256((token + ".napcat").encode("utf-8")).hexdigest()

    async def login(self) -> str:
        if self._credential:
            return self._credential
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self.base_url}/api/auth/login",
                json={"hash": self._token_hash()},
            )
            resp.raise_for_status()
            data = resp.json()
            credential = (((data or {}).get("data") or {}).get("Credential")) if isinstance(data, dict) else None
            if not credential:
                raise RuntimeError(f"NapCat WebUI login failed: {data}")
            self._credential = str(credential)
            return self._credential

    async def request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        credential = await self.login()
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                json=payload or {},
                headers={"Authorization": f"Bearer {credential}"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_login_info(self) -> dict[str, Any]:
        return await self.request("/api/QQLogin/GetQQLoginInfo")

    async def refresh_qrcode(self) -> dict[str, Any]:
        return await self.request("/api/QQLogin/RefreshQRcode")

    async def get_qrcode(self) -> dict[str, Any]:
        return await self.request("/api/QQLogin/GetQQLoginQrcode")

    async def password_login(self, uin: str, password_md5: str) -> dict[str, Any]:
        return await self.request("/api/QQLogin/PasswordLogin", {"uin": uin, "passwordMd5": password_md5})

    async def captcha_login(self, uin: str, password_md5: str, ticket: str, randstr: str, sid: str = "") -> dict[str, Any]:
        return await self.request(
            "/api/QQLogin/CaptchaLogin",
            {"uin": uin, "passwordMd5": password_md5, "ticket": ticket, "randstr": randstr, "sid": sid},
        )

    async def new_device_login(self, uin: str, password_md5: str, new_device_pull_qrcode_sig: str) -> dict[str, Any]:
        return await self.request(
            "/api/QQLogin/NewDeviceLogin",
            {"uin": uin, "passwordMd5": password_md5, "newDevicePullQrCodeSig": new_device_pull_qrcode_sig},
        )

    async def get_new_device_qrcode(self, uin: str, jump_url: str) -> dict[str, Any]:
        return await self.request(
            "/api/QQLogin/GetNewDeviceQRCode",
            {"uin": uin, "jumpUrl": jump_url},
        )

    async def poll_new_device_qr(self, uin: str, bytes_token: str) -> dict[str, Any]:
        return await self.request(
            "/api/QQLogin/PollNewDeviceQR",
            {"uin": uin, "bytesToken": bytes_token},
        )
