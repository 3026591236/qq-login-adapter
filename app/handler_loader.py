from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Any

from .router import EventRouter


def load_user_handlers(router: EventRouter, package: str = "user_handlers") -> dict[str, Any]:
    """Discover and import user handler modules.

    User modules should import `router` via injection (see below) and call `register(...)`.

    We keep it intentionally simple: any module under `user_handlers` can define a
    `register(router: EventRouter) -> None`.
    """

    loaded: list[str] = []
    errors: dict[str, str] = {}

    try:
        pkg = importlib.import_module(package)
    except Exception as exc:
        return {"ok": True, "loaded": loaded, "errors": {package: str(exc)}, "message": "user_handlers package not found"}

    if not hasattr(pkg, "__path__"):
        return {"ok": True, "loaded": loaded, "errors": {}, "message": "user_handlers is not a package"}

    for m in pkgutil.iter_modules(pkg.__path__, package + "."):
        name = m.name
        try:
            mod = importlib.import_module(name)
            _try_register(mod, router)
            loaded.append(name)
        except Exception as exc:
            errors[name] = str(exc)

    return {"ok": True, "loaded": loaded, "errors": errors}


def _try_register(mod: ModuleType, router: EventRouter) -> None:
    fn = getattr(mod, "register", None)
    if callable(fn):
        fn(router)
