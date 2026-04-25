"""Y43: supplier execution request/attempt persistence and repository validation."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from app.models import SupplierExecutionAttempt, SupplierExecutionRequest
from app.models.enums import (
    OperatorWorkflowIntent,
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierExecutionSourceEntryPoint,
)
from app.repositories import supplier_execution as se_repo
from tests.unit.base import FoundationDBTestCase


class TestSupplierExecutionPersistence(FoundationDBTestCase):
    def test_mappers_load_with_supplier_execution_models(self) -> None:
        import app.models  # noqa: F401

        configure_mappers()
        m = inspect(SupplierExecutionRequest)
        self.assertIn("idempotency_key", m.columns.keys())

    def test_validate_rejects_empty_idempotency(self) -> None:
        with self.assertRaisesRegex(ValueError, "idempotency_key"):
            se_repo.validate_new_execution_request(idempotency_key="   ", source_entity_id=1)

    def test_validate_rejects_non_positive_source_entity_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_entity_id"):
            se_repo.validate_new_execution_request(idempotency_key="k1", source_entity_id=0)

    def test_create_request_and_attempt_roundtrip(self) -> None:
        user = self.create_user()
        req = se_repo.build_execution_request(
            source_entry_point=SupplierExecutionSourceEntryPoint.ADMIN_EXPLICIT,
            source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
            source_entity_id=42,
            idempotency_key="idem-y43-test-1",
            requested_by_user_id=user.id,
            operator_workflow_intent_snapshot=OperatorWorkflowIntent.NEED_SUPPLIER_OFFER,
        )
        se_repo.add_execution_request(self.session, req)
        self.assertIsNotNone(req.id)
        self.assertEqual(req.status, SupplierExecutionRequestStatus.PENDING)
        self.assertEqual(req.source_entity_id, 42)
        self.assertIsNotNone(req.created_at)
        at = se_repo.build_execution_attempt(
            execution_request_id=req.id,
            attempt_number=1,
            channel_type=SupplierExecutionAttemptChannel.NONE,
            status=SupplierExecutionAttemptStatus.SKIPPED,
            created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        se_repo.add_execution_attempt(self.session, at)
        self.assertIsNotNone(at.id)
        self.session.refresh(req)
        self.assertEqual(len(req.attempts), 1)

    def test_idempotency_key_unique(self) -> None:
        u = self.create_user()
        r1 = se_repo.build_execution_request(
            source_entry_point=SupplierExecutionSourceEntryPoint.OPERATOR_DO_ACTION,
            source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
            source_entity_id=99,
            idempotency_key="same-key-twice",
            requested_by_user_id=u.id,
        )
        r2 = se_repo.build_execution_request(
            source_entry_point=SupplierExecutionSourceEntryPoint.OPERATOR_DO_ACTION,
            source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
            source_entity_id=100,
            idempotency_key="same-key-twice",
            requested_by_user_id=u.id,
        )
        se_repo.add_execution_request(self.session, r1)
        with self.assertRaises(IntegrityError):
            se_repo.add_execution_request(self.session, r2)
        self.session.rollback()
        r3 = se_repo.build_execution_request(
            source_entry_point=SupplierExecutionSourceEntryPoint.OPERATOR_DO_ACTION,
            source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
            source_entity_id=2,
            idempotency_key="same-key-twice-ok",
        )
        se_repo.add_execution_request(self.session, r3)
        self.assertIsNotNone(r3.id)

    def test_db_rejects_zero_source_entity_id(self) -> None:
        u = self.create_user()
        bad = SupplierExecutionRequest(
            source_entry_point=SupplierExecutionSourceEntryPoint.SCHEDULED_JOB,
            source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
            source_entity_id=0,
            idempotency_key="ck-zero",
            status=SupplierExecutionRequestStatus.PENDING,
            requested_by_user_id=u.id,
        )
        self.session.add(bad)
        with self.assertRaises(IntegrityError):
            self.session.flush()
        self.session.rollback()

    def test_add_execution_request_validates(self) -> None:
        u = self.create_user()
        bad = se_repo.build_execution_request(
            source_entry_point=SupplierExecutionSourceEntryPoint.ADMIN_EXPLICIT,
            source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
            source_entity_id=1,
            idempotency_key="  ",
            requested_by_user_id=u.id,
        )
        with self.assertRaisesRegex(ValueError, "idempotency_key"):
            se_repo.add_execution_request(self.session, bad)

    def test_build_attempt_rejects_invalid_execution_request_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "execution_request_id"):
            se_repo.build_execution_attempt(
                execution_request_id=0,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.INTERNAL,
                status=SupplierExecutionAttemptStatus.PENDING,
            )

    def test_build_attempt_rejects_invalid_attempt_number(self) -> None:
        with self.assertRaisesRegex(ValueError, "attempt_number"):
            se_repo.build_execution_attempt(
                execution_request_id=1,
                attempt_number=0,
                channel_type=SupplierExecutionAttemptChannel.INTERNAL,
                status=SupplierExecutionAttemptStatus.PENDING,
            )


if __name__ == "__main__":
    unittest.main()
