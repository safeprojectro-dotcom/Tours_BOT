"""B16D2A: admin guarded action audit + idempotency foundation (no business mutations)."""

from __future__ import annotations

import unittest

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.admin_guarded_action import AdminGuardedActionStep
from app.models.enums import AdminGuardedActionAttemptStatus, AdminGuardedActionStepStatus
from app.repositories.admin_guarded_action import attempt_repository
from app.services.admin_guarded_action_audit_service import (
    ACTION_PREPARE_CONVERSION_CHAIN,
    SOURCE_ENTITY_SUPPLIER_OFFER,
    AdminGuardedActionAuditService,
)
from tests.unit.base import FoundationDBTestCase


class AdminGuardedActionAuditTests(FoundationDBTestCase):
    def test_get_or_create_attempt_is_idempotent(self) -> None:
        svc = AdminGuardedActionAuditService()
        a1, created1 = svc.get_or_create_attempt(
            self.session,
            action_code=ACTION_PREPARE_CONVERSION_CHAIN,
            source_entity_type=SOURCE_ENTITY_SUPPLIER_OFFER,
            source_entity_id=99,
            idempotency_key="  key-one  ",
            requested_by="admin:test",
            dry_run=False,
        )
        self.assertTrue(created1)
        self.assertEqual(a1.idempotency_key, "key-one")
        self.assertEqual(a1.status, AdminGuardedActionAttemptStatus.PENDING.value)

        a2, created2 = svc.get_or_create_attempt(
            self.session,
            action_code=ACTION_PREPARE_CONVERSION_CHAIN,
            source_entity_type=SOURCE_ENTITY_SUPPLIER_OFFER,
            source_entity_id=99,
            idempotency_key="key-one",
        )
        self.assertFalse(created2)
        self.assertEqual(a1.id, a2.id)

    def test_duplicate_insert_violates_unique_constraint(self) -> None:
        attempt_repository.add_attempt(
            self.session,
            data={
                "action_code": ACTION_PREPARE_CONVERSION_CHAIN,
                "source_entity_type": SOURCE_ENTITY_SUPPLIER_OFFER,
                "source_entity_id": 42,
                "idempotency_key": "dup-key",
                "status": AdminGuardedActionAttemptStatus.PENDING.value,
                "dry_run": False,
            },
        )
        with self.session.begin_nested():
            with self.assertRaises(IntegrityError):
                attempt_repository.add_attempt(
                    self.session,
                    data={
                        "action_code": ACTION_PREPARE_CONVERSION_CHAIN,
                        "source_entity_type": SOURCE_ENTITY_SUPPLIER_OFFER,
                        "source_entity_id": 42,
                        "idempotency_key": "dup-key",
                        "status": AdminGuardedActionAttemptStatus.PENDING.value,
                        "dry_run": False,
                    },
                )

    def test_steps_and_status_updates(self) -> None:
        svc = AdminGuardedActionAuditService()
        attempt, _ = svc.get_or_create_attempt(
            self.session,
            action_code=ACTION_PREPARE_CONVERSION_CHAIN,
            source_entity_type=SOURCE_ENTITY_SUPPLIER_OFFER,
            source_entity_id=7,
            idempotency_key="idem-steps",
            dry_run=True,
        )
        self.assertTrue(attempt.dry_run)

        s1 = svc.create_step(
            self.session,
            attempt=attempt,
            step_code="ensure_tour_bridge",
            step_order=1,
            detail={"planned": True},
        )
        s2 = svc.create_step(
            self.session,
            attempt=attempt,
            step_code="activate_catalog",
            step_order=2,
        )
        self.assertEqual(s1.status, AdminGuardedActionStepStatus.PENDING.value)

        svc.set_step_running(self.session, s1)
        self.assertEqual(s1.status, AdminGuardedActionStepStatus.RUNNING.value)
        self.assertIsNotNone(s1.started_at)

        svc.complete_step(self.session, s1, status=AdminGuardedActionStepStatus.SUCCEEDED)
        svc.set_step_running(self.session, s2)
        svc.complete_step(
            self.session,
            s2,
            status=AdminGuardedActionStepStatus.FAILED,
            error_code="test_fail",
            error_message="no business mutation in B16D2A",
        )

        svc.set_attempt_status(self.session, attempt, status=AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS)

        self.session.refresh(attempt)
        rows = list(
            self.session.scalars(
                select(AdminGuardedActionStep)
                .where(AdminGuardedActionStep.attempt_id == attempt.id)
                .order_by(AdminGuardedActionStep.step_order)
            ).all()
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].status, AdminGuardedActionStepStatus.SUCCEEDED.value)
        self.assertEqual(rows[1].status, AdminGuardedActionStepStatus.FAILED.value)
        self.assertEqual(attempt.status, AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS.value)

    def test_validate_idempotency_key_rejects_blank(self) -> None:
        svc = AdminGuardedActionAuditService()
        with self.assertRaisesRegex(ValueError, "idempotency_key"):
            svc.get_or_create_attempt(
                self.session,
                action_code=ACTION_PREPARE_CONVERSION_CHAIN,
                source_entity_type=SOURCE_ENTITY_SUPPLIER_OFFER,
                source_entity_id=1,
                idempotency_key="   ",
            )

    def test_step_order_unique(self) -> None:
        svc = AdminGuardedActionAuditService()
        attempt, _ = svc.get_or_create_attempt(
            self.session,
            action_code=ACTION_PREPARE_CONVERSION_CHAIN,
            source_entity_type=SOURCE_ENTITY_SUPPLIER_OFFER,
            source_entity_id=3,
            idempotency_key="order-test",
        )
        svc.create_step(self.session, attempt=attempt, step_code="a", step_order=1)
        with self.session.begin_nested():
            with self.assertRaises(IntegrityError):
                svc.create_step(self.session, attempt=attempt, step_code="b", step_order=1)


if __name__ == "__main__":
    unittest.main()
