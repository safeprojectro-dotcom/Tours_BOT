"""Y44 admin read; Y46 safe admin trigger POST (no supplier contact, no attempt rows from trigger). Y50 send-telegram."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models import SupplierExecutionAttempt, SupplierExecutionRequest
from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.user import User
from app.models.enums import (
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    OperatorWorkflowIntent,
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierExecutionSourceEntryPoint,
)
from app.repositories import supplier_execution as se_repo
from app.services.telegram_showcase_client import TelegramShowcaseSendError
from tests.unit.base import FoundationDBTestCase

_ADMIN_HEADERS = {"Authorization": "Bearer test-admin-secret"}


def _actor_headers(telegram_user_id: int) -> dict[str, str]:
    return {
        **_ADMIN_HEADERS,
        "X-Admin-Actor-Telegram-Id": str(telegram_user_id),
    }


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
        self._original_bot_token = get_settings().telegram_bot_token
        get_settings().admin_api_token = "test-admin-secret"
        get_settings().telegram_bot_token = "y50-test-telegram-token"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        get_settings().telegram_bot_token = self._original_bot_token
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _count_requests(self) -> int:
        return self.session.scalar(select(func.count()).select_from(SupplierExecutionRequest)) or 0

    def _count_attempts(self) -> int:
        return self.session.scalar(select(func.count()).select_from(SupplierExecutionAttempt)) or 0

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

    def _make_cmr(self, *, user_tg: int, intent: OperatorWorkflowIntent | None = None) -> CustomMarketplaceRequest:
        u = self.create_user(telegram_user_id=user_tg)
        row = CustomMarketplaceRequest(
            user_id=u.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            route_notes="Y45 route",
            group_size=4,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.UNDER_REVIEW,
            operator_workflow_intent=intent,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def test_y45_post_trigger_requires_actor_header(self) -> None:
        self._make_cmr(user_tg=555_100)
        r = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_ADMIN_HEADERS,
            json={
                "idempotency_key": "y45-actor-1",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": 1,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_y45_post_trigger_unauthorized_without_admin_token(self) -> None:
        r = self.client.post(
            "/admin/supplier-execution-requests",
            json={
                "idempotency_key": "x",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": 1,
            },
        )
        self.assertEqual(r.status_code, 401)

    def test_y45_post_trigger_404_missing_source(self) -> None:
        self.create_user(telegram_user_id=555_101)
        r = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(555_101),
            json={
                "idempotency_key": "y45-miss-1",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": 9_999_999,
            },
        )
        self.assertEqual(r.status_code, 404)

    def test_y45_post_trigger_201_and_idempotent_200(self) -> None:
        cmr = self._make_cmr(
            user_tg=555_201,
            intent=OperatorWorkflowIntent.NEED_MANUAL_FOLLOWUP,
        )
        n0 = self._count_requests()
        p1 = {
            "idempotency_key": "y45-idem-1",
            "source_entity_type": "custom_marketplace_request",
            "source_entity_id": cmr.id,
        }
        r1 = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(555_201),
            json=p1,
        )
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(self._count_requests(), n0 + 1)
        b1 = r1.json()
        self.assertFalse(b1.get("idempotent_replay", True))
        self.assertEqual(b1["request"]["status"], "validated")
        self.assertEqual(b1["request"]["source_entry_point"], "admin_explicit")
        self.assertEqual(b1["request"]["idempotency_key"], "y45-idem-1")
        self.assertEqual(b1["request"]["operator_workflow_intent_snapshot"], "need_manual_followup")
        req_user = self.session.scalars(select(User).where(User.telegram_user_id == 555_201)).first()
        self.assertIsNotNone(req_user)
        self.assertEqual(b1["request"]["requested_by_user_id"], req_user.id)

        r2 = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(555_201),
            json=p1,
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(self._count_requests(), n0 + 1)
        b2 = r2.json()
        self.assertTrue(b2.get("idempotent_replay", False))
        self.assertEqual(b2["request"]["id"], b1["request"]["id"])

    def test_y45_idempotency_key_conflict_409(self) -> None:
        a = self._make_cmr(user_tg=555_301)
        b = self._make_cmr(user_tg=555_302)
        key = "y45-same-key-conflict"
        r_ok = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(555_301),
            json={
                "idempotency_key": key,
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": a.id,
            },
        )
        self.assertEqual(r_ok.status_code, 201)
        r_bad = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(555_301),
            json={
                "idempotency_key": key,
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": b.id,
            },
        )
        self.assertEqual(r_bad.status_code, 409)

    def test_y46_post_503_when_admin_token_disabled(self) -> None:
        get_settings().admin_api_token = None
        r = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(999_001),
            json={
                "idempotency_key": "y46-503",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": 1,
            },
        )
        self.assertEqual(r.status_code, 503)
        get_settings().admin_api_token = "test-admin-secret"

    def test_y46_post_422_blank_idempotency_key(self) -> None:
        self.create_user(telegram_user_id=556_001)
        r = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(556_001),
            json={
                "idempotency_key": "   ",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": 1,
            },
        )
        self.assertEqual(r.status_code, 422)

    def test_y46_post_creates_no_attempt_rows(self) -> None:
        cmr = self._make_cmr(user_tg=556_101)
        na = self._count_attempts()
        r = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(556_101),
            json={
                "idempotency_key": "y46-no-attempts",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": cmr.id,
            },
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self._count_attempts(), na)
        self.assertEqual(len(r.json()["request"]["attempts"]), 0)

    def test_y46_post_does_not_mutate_source_cmr(self) -> None:
        cmr = self._make_cmr(user_tg=556_201, intent=OperatorWorkflowIntent.NEED_SUPPLIER_OFFER)
        before_notes = cmr.route_notes
        before_status = cmr.status
        self.session.expire(cmr)
        r = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(556_201),
            json={
                "idempotency_key": "y46-cmr-readonly",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": cmr.id,
            },
        )
        self.assertEqual(r.status_code, 201)
        self.session.refresh(cmr)
        self.assertEqual(cmr.route_notes, before_notes)
        self.assertEqual(cmr.status, before_status)

    def _add_execution_request(
        self,
        *,
        idem: str,
        user_id: int,
        ent_id: int = 1,
        status: SupplierExecutionRequestStatus = SupplierExecutionRequestStatus.VALIDATED,
    ) -> SupplierExecutionRequest:
        return se_repo.add_execution_request(
            self.session,
            se_repo.build_execution_request(
                source_entry_point=SupplierExecutionSourceEntryPoint.ADMIN_EXPLICIT,
                source_entity_type=SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST,
                source_entity_id=ent_id,
                idempotency_key=idem,
                status=status,
                requested_by_user_id=user_id,
            ),
        )

    def test_y48_post_attempt_404_unknown_request(self) -> None:
        u = self.create_user(telegram_user_id=557_001)
        r = self.client.post(
            "/admin/supplier-execution-requests/9999999/attempts",
            headers=_actor_headers(557_001),
        )
        self.assertEqual(r.status_code, 404)

    def test_y48_post_attempt_400_when_request_blocked(self) -> None:
        u = self.create_user(telegram_user_id=557_101)
        er = self._add_execution_request(
            idem="y48-blocked",
            user_id=u.id,
            ent_id=1,
            status=SupplierExecutionRequestStatus.BLOCKED,
        )
        r = self.client.post(
            f"/admin/supplier-execution-requests/{er.id}/attempts",
            headers=_actor_headers(557_101),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("blocked", r.json()["detail"].lower())

    def test_y48_post_attempt_201_increments_attempt_number(self) -> None:
        u = self.create_user(telegram_user_id=557_201)
        er = self._add_execution_request(idem="y48-multi", user_id=u.id, ent_id=1)
        a0 = self._count_attempts()
        r1 = self.client.post(
            f"/admin/supplier-execution-requests/{er.id}/attempts",
            headers=_actor_headers(557_201),
        )
        self.assertEqual(r1.status_code, 201)
        b1 = r1.json()
        self.assertEqual(b1["attempt_number"], 1)
        self.assertEqual(b1["status"], "pending")
        self.assertEqual(b1["channel_type"], "none")
        self.assertEqual(b1["execution_request_id"], er.id)
        self.assertEqual(self._count_attempts(), a0 + 1)
        r2 = self.client.post(
            f"/admin/supplier-execution-requests/{er.id}/attempts",
            headers=_actor_headers(557_201),
        )
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r2.json()["attempt_number"], 2)
        self.assertEqual(self._count_attempts(), a0 + 2)

    def test_y48_post_attempt_does_not_change_request_status(self) -> None:
        u = self.create_user(telegram_user_id=557_301)
        er = self._add_execution_request(
            idem="y48-status-unch",
            user_id=u.id,
            ent_id=1,
            status=SupplierExecutionRequestStatus.VALIDATED,
        )
        st_before = er.status
        r = self.client.post(
            f"/admin/supplier-execution-requests/{er.id}/attempts",
            headers=_actor_headers(557_301),
        )
        self.assertEqual(r.status_code, 201)
        self.session.refresh(er)
        self.assertEqual(er.status, st_before)
        self.assertEqual(er.status, SupplierExecutionRequestStatus.VALIDATED)

    def test_y48_post_attempt_401_without_admin(self) -> None:
        u = self.create_user(telegram_user_id=557_401)
        er = self._add_execution_request(idem="y48-auth", user_id=u.id, ent_id=1)
        r = self.client.post(f"/admin/supplier-execution-requests/{er.id}/attempts")
        self.assertEqual(r.status_code, 401)

    def test_y48_post_attempt_503_admin_disabled(self) -> None:
        u = self.create_user(telegram_user_id=557_501)
        er = self._add_execution_request(idem="y48-503", user_id=u.id, ent_id=1)
        get_settings().admin_api_token = None
        r = self.client.post(
            f"/admin/supplier-execution-requests/{er.id}/attempts",
            headers=_actor_headers(557_501),
        )
        self.assertEqual(r.status_code, 503)
        get_settings().admin_api_token = "test-admin-secret"

    def _y50_post_send(
        self,
        *,
        attempt_id: int,
        actor_tg: int,
        idempotency: str = "y50-k",
        text: str = "Hello supplier",
        target: int = 88_001,
    ):
        return self.client.post(
            f"/admin/supplier-execution-attempts/{attempt_id}/send-telegram",
            headers=_actor_headers(actor_tg),
            json={
                "idempotency_key": idempotency,
                "message_text": text,
                "target_telegram_user_id": target,
            },
        )

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=42_001)
    def test_y50_send_401_without_admin(self, _mock) -> None:
        r = self.client.post(
            "/admin/supplier-execution-attempts/1/send-telegram",
            json={"idempotency_key": "a", "message_text": "m", "target_telegram_user_id": 1},
        )
        self.assertEqual(r.status_code, 401)

    def test_y50_send_400_missing_idempotency(self) -> None:
        u = self.create_user(telegram_user_id=560_100)
        er = self._add_execution_request(idem="y50-mi", user_id=u.id, ent_id=1)
        att = se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=er.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.PENDING,
            ),
        )
        self.session.flush()
        r = self.client.post(
            f"/admin/supplier-execution-attempts/{att.id}/send-telegram",
            headers=_actor_headers(560_100),
            json={"message_text": "x", "target_telegram_user_id": 1},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("idempotency", r.json()["detail"].lower())

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=1)
    def test_y50_send_404_unknown_attempt(self, _mock) -> None:
        u = self.create_user(telegram_user_id=560_101)
        self._add_execution_request(idem="y50-404r", user_id=u.id, ent_id=1)
        r = self._y50_post_send(attempt_id=99_999_999, actor_tg=560_101)
        self.assertEqual(r.status_code, 404)

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=1)
    def test_y50_send_400_non_pending_attempt(self, _mock) -> None:
        u = self.create_user(telegram_user_id=560_102)
        er = self._add_execution_request(idem="y50-skip", user_id=u.id, ent_id=1)
        att = se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=er.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.SKIPPED,
            ),
        )
        self.session.flush()
        r = self._y50_post_send(attempt_id=att.id, actor_tg=560_102)
        self.assertEqual(r.status_code, 400)
        self.assertIn("pending", r.json()["detail"].lower())
        _mock.assert_not_called()  # type: ignore[attr-defined]

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=42_001)
    def test_y50_send_201_success_and_stores_provider_ref(self, mock_send) -> None:
        u = self.create_user(telegram_user_id=560_103)
        er = self._add_execution_request(idem="y50-ok", user_id=u.id, ent_id=1)
        a = se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=er.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.PENDING,
            ),
        )
        self.session.flush()
        r = self._y50_post_send(attempt_id=a.id, actor_tg=560_103, idempotency="y50-idem-1", target=77_123)
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertFalse(body.get("idempotent_replay", True))
        at = body["attempt"]
        self.assertEqual(at["status"], "succeeded")
        self.assertEqual(at["channel_type"], "telegram")
        self.assertEqual(at["provider_reference"], "42001")
        self.assertEqual(at["target_supplier_ref"], "77123")
        mock_send.assert_called_once()
        self.session.refresh(a)
        self.assertEqual(a.status, SupplierExecutionAttemptStatus.SUCCEEDED)
        self.assertEqual(a.provider_reference, "42001")

    @patch(
        "app.services.admin_supplier_execution_telegram_send.send_private_text_message",
        side_effect=TelegramShowcaseSendError("telegram failed", telegram_description="bot blocked"),
    )
    def test_y50_send_failure_marks_failed_and_stores_error(self, mock_send) -> None:
        u = self.create_user(telegram_user_id=560_104)
        er = self._add_execution_request(idem="y50-fail", user_id=u.id, ent_id=1)
        a = se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=er.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.PENDING,
            ),
        )
        self.session.flush()
        r = self._y50_post_send(attempt_id=a.id, actor_tg=560_104, idempotency="y50-fail-1")
        self.assertEqual(r.status_code, 200)
        at = r.json()["attempt"]
        self.assertEqual(at["status"], "failed")
        self.assertEqual(at["error_code"], "telegram_send_failed")
        self.assertIn("blocked", (at.get("error_message") or ""))
        mock_send.assert_called_once()
        self.session.refresh(a)
        self.assertEqual(a.status, SupplierExecutionAttemptStatus.FAILED)

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=99)
    def test_y50_idempotent_replay_no_second_send(self, mock_send) -> None:
        u = self.create_user(telegram_user_id=560_105)
        er = self._add_execution_request(idem="y50-id2", user_id=u.id, ent_id=1)
        a = se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=er.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.PENDING,
            ),
        )
        self.session.flush()
        r1 = self._y50_post_send(attempt_id=a.id, actor_tg=560_105, idempotency="idem-same", target=55_001)
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(mock_send.call_count, 1)
        r2 = self._y50_post_send(attempt_id=a.id, actor_tg=560_105, idempotency="idem-same", target=55_001)
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json().get("idempotent_replay", False))
        self.assertEqual(mock_send.call_count, 1)
        self.assertEqual(r1.json()["attempt"]["id"], r2.json()["attempt"]["id"])
        self.assertEqual(r1.json()["attempt"]["provider_reference"], r2.json()["attempt"]["provider_reference"])

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=0)
    def test_y50_request_and_attempt_creation_do_not_call_telegram(self, mock_send) -> None:
        cmr = self._make_cmr(user_tg=560_201, intent=OperatorWorkflowIntent.NEED_MANUAL_FOLLOWUP)
        r1 = self.client.post(
            "/admin/supplier-execution-requests",
            headers=_actor_headers(560_201),
            json={
                "idempotency_key": "y50-nosend-r",
                "source_entity_type": "custom_marketplace_request",
                "source_entity_id": cmr.id,
            },
        )
        self.assertEqual(r1.status_code, 201)
        er_id = r1.json()["request"]["id"]
        r2 = self.client.post(
            f"/admin/supplier-execution-requests/{er_id}/attempts",
            headers=_actor_headers(560_201),
        )
        self.assertEqual(r2.status_code, 201)
        mock_send.assert_not_called()

    @patch("app.services.admin_supplier_execution_telegram_send.send_private_text_message", return_value=0)
    def test_y50_503_no_bot_token(self, _mock) -> None:
        u = self.create_user(telegram_user_id=560_106)
        er = self._add_execution_request(idem="y50-503b", user_id=u.id, ent_id=1)
        a = se_repo.add_execution_attempt(
            self.session,
            se_repo.build_execution_attempt(
                execution_request_id=er.id,
                attempt_number=1,
                channel_type=SupplierExecutionAttemptChannel.NONE,
                status=SupplierExecutionAttemptStatus.PENDING,
            ),
        )
        self.session.flush()
        get_settings().telegram_bot_token = None
        r = self._y50_post_send(attempt_id=a.id, actor_tg=560_106, idempotency="x")
        self.assertEqual(r.status_code, 503)
        get_settings().telegram_bot_token = "y50-test-telegram-token"
