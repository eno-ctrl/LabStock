import json
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from backend.app.core.logging import redact_dict
from backend.app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: int | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        clean_details = None
        if details:
            redacted = redact_dict(details)
            clean_details = json.dumps(redacted, default=str)

        log = AuditLog(
            action=action.strip().upper(),
            entity_type=entity_type.strip().lower(),
            entity_id=str(entity_id),
            actor_id=actor_id,
            request_id=request_id,
            details_json=clean_details,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(self, skip: int = 0, limit: int = 50) -> tuple[list[AuditLog], int]:
        q = self.db.query(AuditLog).options(joinedload(AuditLog.actor))
        total = q.count()
        logs = q.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
        return logs, total
