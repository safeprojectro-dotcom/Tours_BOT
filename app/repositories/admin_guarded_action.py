"""B16D2A: repository helpers for admin guarded action audit rows."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_guarded_action import AdminGuardedActionAttempt, AdminGuardedActionStep


class AdminGuardedActionAttemptRepository:
    def get_by_idempotency(
        self,
        session: Session,
        *,
        action_code: str,
        source_entity_type: str,
        source_entity_id: int,
        idempotency_key: str,
    ) -> AdminGuardedActionAttempt | None:
        stmt = select(AdminGuardedActionAttempt).where(
            AdminGuardedActionAttempt.action_code == action_code,
            AdminGuardedActionAttempt.source_entity_type == source_entity_type,
            AdminGuardedActionAttempt.source_entity_id == source_entity_id,
            AdminGuardedActionAttempt.idempotency_key == idempotency_key,
        )
        return session.scalar(stmt)

    def add_attempt(self, session: Session, *, data: dict[str, Any]) -> AdminGuardedActionAttempt:
        row = AdminGuardedActionAttempt(**data)
        session.add(row)
        session.flush()
        session.refresh(row)
        return row

    def add_step(self, session: Session, *, data: dict[str, Any]) -> AdminGuardedActionStep:
        row = AdminGuardedActionStep(**data)
        session.add(row)
        session.flush()
        session.refresh(row)
        return row


attempt_repository = AdminGuardedActionAttemptRepository()
