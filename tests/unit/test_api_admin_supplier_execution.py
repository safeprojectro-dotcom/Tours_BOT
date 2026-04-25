"""Y44: read-only admin API for supplier execution requests — no mutation paths."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models import SupplierExecutionRequest
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

_ADMIN_HEADERS = {"Authorization": "Bearer test-admin-secret"}


class AdminSupplierExecutionReadRouteTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction) -> None:
            parent = getattr(transaction, "_parent", None)
            if transaction.nested and not getattr(parent, "nested", False):
                self.nested = self.connection.begin_nested()

        self._restart_savepoint = restart_savepoint
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _count_requests(self) -> int:
        return self.session.scalar(select(func.count()).select_from(SupplierExecutionRequest)) or 0

    def test_admin_unauthorized_without_token(self) -> None:
        r = self.client.get("/admin/supplier-execution-requests")
        self.assertEqual(r.status_code, 401)

    def test_admin_invalid_token(self) -> None:
        r = self.client.get(
            "/admin/supplier-execution-requests",
            headers={"Authorization": "Bearer wrong"},
        )
        self.assertEqual(r.status_code, 401)

    def test_admin_503_without_configured_token(self) -> None:
        get_settings().admin_api_token = None
        r = self.client.get("/admin/supplier-execution-requests", headers=_ADMIN_HEADERS)
        self.assertEqual(r.status_code, 503)
        get_settings().admin_api_token = "test-admin-secret"

    def test_list_and_detail_read_only(self) -> None:
        user = self.create_user()
        r1 = se_repo.add_execution_request(
            self.session,
            se_repo.build_execution_request(
                source_entry_point=SupplierExecutionSourceEntryPoint.ADMIN_EXPLICIT,
                source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
                source_entity_id=7,
                idempotency_key="y44-list-1",
                requested_by_user_id=user.id,
                status=SupplierExecutionRequestStatus.PENDING,
                operator_workflow_intent_snapshot=OperatorWorkflowIntent.NEED_SUPPLIER_OFFER,
            ),
        )
        r2 = se_repo.add_execution_request(
            self.session,
            se_repo.build_execution_request(
                source_entry_point=SupplierExecutionSourceEntryPoint.OPERATOR_DO_ACTION,
                source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
                source_entity_id=8,
                idempotency_key="y44-list-2",
                requested_by_user_id=user.id,
                status=SupplierExecutionRequestStatus.VALIDATED,
            ),
        )
        se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=r1.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.SKIPPED,
            ),
        )
        n_before = self._count_requests()
        le = self.client.get("/admin/supplier-execution-requests", headers=_ADMIN_HEADERS)
        self.assertEqual(le.status_code, 200)
        self.assertEqual(self._count_requests(), n_before)
        body = le.json()
        self.assertIn("items", body)
        self.assertEqual(len(body["items"]), 2)
        self.assertEqual(body["total_returned"], 2)
        f_pending = self.client.get(
            "/admin/supplier-execution-requests",
            headers=_ADMIN_HEADERS,
            params={"status": "pending"},
        )
        self.assertEqual(f_pending.status_code, 200)
        self.assertEqual(len(f_pending.json()["items"]), 1)
        f_type = self.client.get(
            "/admin/supplier-execution-requests",
            headers=_ADMIN_HEADERS,
            params={"source_entity_type": "custom_marketplace_request", "offset": 0, "limit": 10},
        )
        self.assertEqual(f_type.status_code, 200)
        self.assertEqual(len(f_type.json()["items"]), 2)
        d = self.client.get(f"/admin/supplier-execution-requests/{r1.id}", headers=_ADMIN_HEADERS)
        self.assertEqual(d.status_code, 200)
        dbody = d.json()
        self.assertEqual(dbody["id"], r1.id)
        self.assertEqual(dbody["source_entity_id"], 7)
        self.assertEqual(dbody["operator_workflow_intent_snapshot"], "need_supplier_offer")
        self.assertEqual(len(dbody["attempts"]), 1)
        self.assertEqual(dbody["attempts"][0]["attempt_number"], 1)
        self.assertEqual(dbody["attempts"][0]["status"], "skipped")
        self.assertEqual(self._count_requests(), n_before)

    def test_detail_404(self) -> None:
        r = self.client.get("/admin/supplier-execution-requests/999999", headers=_ADMIN_HEADERS)
        self.assertEqual(r.status_code, 404)
