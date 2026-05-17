"""A4: supplier clarification outbox API (internal persistence only; no supplier send)."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.supplier_clarification_outbox import SupplierClarificationOutboxItem
from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead
from tests.unit.base import FoundationDBTestCase


class SupplierClarificationOutboxApiTests(FoundationDBTestCase):
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

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def _post_draft(self, offer_id: int, **overrides) -> dict:
        fields = {
            "supplier_offer_id": offer_id,
            "supplier_facing_asks": ["Vă rugăm să confirmați prețul pentru această ofertă."],
            "supplier_facing_message_ro": None,
            "internal_admin_tasks": ["prepare_chain:blocked"],
        }
        fields.update(overrides)
        draft = SupplierClarificationDraftRead(**fields)
        r = self.client.post(
            "/admin/supplier-clarification-outbox",
            headers=self._headers(),
            json={
                "draft": draft.model_dump(mode="json"),
                "created_by_telegram_user_id": 424242,
            },
        )
        self.assertEqual(r.status_code, 200 if r.json().get("replayed_existing") else 201, r.text)
        return r.json()

    def test_post_list_get_outbox_happy_path(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        draft = SupplierClarificationDraftRead(
            supplier_offer_id=offer.id,
            supplier_facing_asks=["Vă rugăm să confirmați prețul pentru această ofertă."],
            supplier_facing_message_ro=None,
            internal_admin_tasks=["prepare_chain:blocked"],
        )
        r = self.client.post(
            "/admin/supplier-clarification-outbox",
            headers=self._headers(),
            json={
                "draft": draft.model_dump(mode="json"),
                "created_by_telegram_user_id": 424242,
            },
        )
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertFalse(data["replayed_existing"])
        item = data["item"]
        self.assertEqual(item["supplier_offer_id"], offer.id)
        self.assertEqual(item["workflow_status"], "draft")
        self.assertIn("supplier_facing_asks", item["draft_snapshot"])
        item_id = item["id"]

        r2 = self.client.get(
            f"/admin/supplier-clarification-outbox?supplier_offer_id={offer.id}",
            headers=self._headers(),
        )
        self.assertEqual(r2.status_code, 200)
        rows = r2.json()
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], item_id)

        r3 = self.client.get(f"/admin/supplier-clarification-outbox/{item_id}", headers=self._headers())
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["id"], item_id)

    def test_post_replays_active_draft_no_duplicate(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        first = self._post_draft(offer.id)
        self.assertFalse(first["replayed_existing"])
        id1 = first["item"]["id"]

        second = self._post_draft(offer.id)
        self.assertTrue(second["replayed_existing"])
        self.assertEqual(second["item"]["id"], id1)

        r = self.client.post(
            "/admin/supplier-clarification-outbox",
            headers=self._headers(),
            json={
                "draft": SupplierClarificationDraftRead(
                    supplier_offer_id=offer.id,
                    supplier_facing_asks=[],
                ).model_dump(mode="json"),
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["replayed_existing"])
        self.assertEqual(body["item"]["id"], id1)

    def test_post_replays_ready_for_review(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        row = SupplierClarificationOutboxItem(
            supplier_offer_id=offer.id,
            workflow_status="ready_for_review",
            draft_snapshot={"x": 1},
        )
        self.session.add(row)
        self.session.flush()

        data = self._post_draft(offer.id, supplier_facing_asks=["new ask"])
        self.assertTrue(data["replayed_existing"])
        self.assertEqual(data["item"]["id"], row.id)

    def test_post_after_cancelled_creates_new(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        old = SupplierClarificationOutboxItem(
            supplier_offer_id=offer.id,
            workflow_status="cancelled",
            draft_snapshot={"old": True},
        )
        self.session.add(old)
        self.session.flush()
        old_id = old.id

        data = self._post_draft(offer.id)
        self.assertFalse(data["replayed_existing"])
        self.assertNotEqual(data["item"]["id"], old_id)
        self.assertEqual(data["item"]["workflow_status"], "draft")

    def test_post_after_sent_externally_later_creates_new(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        old = SupplierClarificationOutboxItem(
            supplier_offer_id=offer.id,
            workflow_status="sent_externally_later",
            draft_snapshot={"old": True},
        )
        self.session.add(old)
        self.session.flush()
        old_id = old.id

        data = self._post_draft(offer.id)
        self.assertFalse(data["replayed_existing"])
        self.assertNotEqual(data["item"]["id"], old_id)

    def test_post_outbox_404_unknown_offer(self) -> None:
        draft = SupplierClarificationDraftRead(
            supplier_offer_id=9_999_999,
            supplier_facing_asks=[],
        )
        r = self.client.post(
            "/admin/supplier-clarification-outbox",
            headers=self._headers(),
            json={"draft": draft.model_dump(mode="json")},
        )
        self.assertEqual(r.status_code, 404)

    def test_get_outbox_item_404(self) -> None:
        r = self.client.get("/admin/supplier-clarification-outbox/999999999", headers=self._headers())
        self.assertEqual(r.status_code, 404)

    def test_patch_outbox_draft_to_ready_for_review(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        created = self._post_draft(offer.id)
        item_id = created["item"]["id"]
        r = self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={
                "workflow_status": "ready_for_review",
                "review_note": "LGTM",
                "reviewed_by_telegram_user_id": 777001,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["workflow_status"], "ready_for_review")
        self.assertEqual(data["review_note"], "LGTM")
        self.assertIsNotNone(data["last_reviewed_at"])
        self.assertEqual(data["last_reviewed_by_telegram_user_id"], 777001)

    def test_patch_outbox_ready_to_sent_externally_later(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        item_id = self._post_draft(offer.id)["item"]["id"]
        self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "ready_for_review"},
        )
        r = self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "sent_externally_later", "review_note": "Emailed supplier"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["workflow_status"], "sent_externally_later")

    def test_patch_outbox_draft_cancelled(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        item_id = self._post_draft(offer.id)["item"]["id"]
        r = self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "cancelled"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["workflow_status"], "cancelled")

    def test_patch_outbox_invalid_transition_422(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        item_id = self._post_draft(offer.id)["item"]["id"]
        r = self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "sent_externally_later"},
        )
        self.assertEqual(r.status_code, 422)
        self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "cancelled"},
        )
        r2 = self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "ready_for_review"},
        )
        self.assertEqual(r2.status_code, 422)

    def test_patch_outbox_review_note_omit_unchanged(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        item_id = self._post_draft(offer.id)["item"]["id"]
        self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "ready_for_review", "review_note": "keep-me"},
        )
        self.client.patch(
            f"/admin/supplier-clarification-outbox/{item_id}",
            headers=self._headers(),
            json={"workflow_status": "sent_externally_later"},
        )
        r = self.client.get(f"/admin/supplier-clarification-outbox/{item_id}", headers=self._headers())
        self.assertEqual(r.json()["review_note"], "keep-me")


if __name__ == "__main__":
    unittest.main()
