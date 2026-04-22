from __future__ import annotations

import subprocess
from pathlib import Path


DEFAULT_CONTAINER_NAME = "napcat"
DEFAULT_CONTAINER_QRCODE_PATH = "/app/napcat/cache/qrcode.png"
DEFAULT_EXPORTED_QRCODE_PATH = Path("/root/.openclaw/workspace/qq-login-adapter/runtime/qrcode.png")


def export_napcat_qrcode(
    container_name: str = DEFAULT_CONTAINER_NAME,
    container_qrcode_path: str = DEFAULT_CONTAINER_QRCODE_PATH,
    exported_path: Path = DEFAULT_EXPORTED_QRCODE_PATH,
) -> dict:
    exported_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["docker", "cp", f"{container_name}:{container_qrcode_path}", str(exported_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    stat = exported_path.stat()
    return {
        "ok": True,
        "path": str(exported_path),
        "size": stat.st_size,
    }
