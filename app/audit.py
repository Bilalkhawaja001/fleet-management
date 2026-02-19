import json
import logging
from datetime import datetime
from pathlib import Path

from flask import current_app, request
from flask_login import current_user

from .models import AuditLog


def log_login(username: str, success: bool, remote_addr: str | None = None):
    """Backward-compatible auth login audit helper."""
    try:
        app_root = Path(current_app.root_path).parent
        logs_dir = app_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger("auth_audit")
        if not logger.handlers:
            fh = logging.FileHandler(logs_dir / "auth_audit.log", encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
            logger.addHandler(fh)
            logger.setLevel(logging.INFO)
        logger.info("login username=%s success=%s ip=%s", username, success, remote_addr or "")
    except Exception:
        # never block auth flow on logging
        pass


def log_audit(module: str, action: str, entity_type: str, entity_id=None, details: dict | None = None):
    actor_user_id = None
    if getattr(current_user, "is_authenticated", False):
        actor_user_id = current_user.id

    ip_addr = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr
    ua = (request.user_agent.string or "")[:300]

    return AuditLog(
        actor_user_id=actor_user_id,
        action=(action or "").strip().lower() or "unknown",
        module=(module or "").strip().lower() or "unknown",
        entity_type=(entity_type or "").strip().lower() or "unknown",
        entity_id=entity_id,
        details_json=json.dumps(details or {}, default=str),
        ip_address=ip_addr,
        user_agent=ua,
        created_at=datetime.utcnow(),
    )
