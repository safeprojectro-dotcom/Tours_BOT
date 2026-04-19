"""Mini App custom request: local validation, schema alignment, FastAPI 422 mapping."""

from __future__ import annotations

import unittest

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.db.session import get_db
from app.main import create_app
from app.schemas.custom_marketplace import MiniAppCustomRequestCreate
from mini_app.custom_request_validation import (
    format_fastapi_422_custom_request,
    message_for_custom_request_422,
    validate_custom_request_form_local,
)
from mini_app.ui_strings import shell
from tests.unit.base import FoundationDBTestCase


class ValidateCustomRequestFormLocalTests(unittest.TestCase):
    def test_ok_minimal(self) -> None:
        self.assertIsNone(
            validate_custom_request_form_local(
                travel_date_start="2026-06-01",
                travel_date_end="",
                route_notes="abc",
                group_size_raw="",
            )
        )

    def test_missing_start(self) -> None:
        self.assertEqual(
            validate_custom_request_form_local(
                travel_date_start="  ",
                travel_date_end="",
                route_notes="abc",
                group_size_raw="",
            ),
            "custom_request_validation_start_date_required",
        )

    def test_invalid_start_iso(self) -> None:
        self.assertEqual(
            validate_custom_request_form_local(
                travel_date_start="not-a-date",
                travel_date_end="",
                route_notes="abc",
                group_size_raw="",
            ),
            "custom_request_validation_start_date_invalid",
        )

    def test_end_before_start(self) -> None:
        self.assertEqual(
            validate_custom_request_form_local(
                travel_date_start="2026-06-10",
                travel_date_end="2026-06-01",
                route_notes="abc",
                group_size_raw="",
            ),
            "custom_request_validation_date_order",
        )

    def test_route_too_short(self) -> None:
        self.assertEqual(
            validate_custom_request_form_local(
                travel_date_start="2026-06-01",
                travel_date_end="",
                route_notes="ab",
                group_size_raw="",
            ),
            "custom_request_validation_route_short",
        )

    def test_group_size_invalid(self) -> None:
        self.assertEqual(
            validate_custom_request_form_local(
                travel_date_start="2026-06-01",
                travel_date_end="",
                route_notes="abc",
                group_size_raw="x",
            ),
            "custom_request_validation_group_size_invalid",
        )


class MiniAppCustomRequestCreateSchemaTests(unittest.TestCase):
    def test_happy_path_payload_matches_api_schema(self) -> None:
        m = MiniAppCustomRequestCreate.model_validate(
            {
                "telegram_user_id": 12345,
                "request_type": "group_trip",
                "travel_date_start": "2026-08-01",
                "travel_date_end": "2026-08-07",
                "route_notes": "Bucharest to Constanta and back",
                "group_size": 4,
                "special_conditions": "  ",
            }
        )
        self.assertEqual(m.travel_date_start.year, 2026)
        self.assertEqual(m.group_size, 4)


class FormatFastApi422CustomRequestTests(unittest.TestCase):
    def test_maps_travel_date_start_loc(self) -> None:
        text = format_fastapi_422_custom_request(
            [
                {
                    "loc": ["body", "travel_date_start"],
                    "msg": "Input should be a valid date or datetime",
                    "type": "date_from_datetime_parsing",
                }
            ],
            "ro",
        )
        self.assertIn("început", text.lower())

    def test_maps_body_model_date_order(self) -> None:
        text = format_fastapi_422_custom_request(
            [
                {
                    "loc": ["body"],
                    "msg": "Value error, travel_date_end must not be before travel_date_start.",
                    "type": "value_error",
                }
            ],
            "ro",
        )
        self.assertIn("sfârșit", text.lower())

    def test_message_for_custom_request_422_uses_response_json(self) -> None:
        req = httpx.Request("POST", "http://test/mini-app/custom-requests")
        resp = httpx.Response(
            422,
            json={
                "detail": [
                    {
                        "loc": ["body", "telegram_user_id"],
                        "msg": "Input should be greater than 0",
                        "type": "greater_than",
                    }
                ]
            },
            request=req,
        )
        exc = httpx.HTTPStatusError("422", request=req, response=resp)
        msg = message_for_custom_request_422(exc, "ro")
        self.assertIn("valid", msg.lower())


class RomanianValidationShellKeysTests(unittest.TestCase):
    def test_validation_keys_exist_ro(self) -> None:
        keys = (
            "custom_request_error_validation_generic",
            "custom_request_validation_start_date_required",
            "custom_request_validation_start_date_invalid",
            "custom_request_validation_end_date_invalid",
            "custom_request_validation_date_order",
            "custom_request_validation_route_short",
            "custom_request_validation_group_size_invalid",
            "custom_request_validation_group_size_range",
            "custom_request_validation_request_type_invalid",
            "custom_request_validation_telegram_user_invalid",
        )
        for k in keys:
            self.assertTrue(len(shell("ro", k)) > 0, k)


class MiniAppCustomRequest422ApiTests(FoundationDBTestCase):
    """POST /mini-app/custom-requests: 422 shape for invalid bodies (DB session required)."""

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

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_empty_travel_date_start_returns_422_with_detail_list(self) -> None:
        self.create_user(telegram_user_id=999_001)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 999_001,
                "request_type": "group_trip",
                "travel_date_start": "",
                "route_notes": "abc",
            },
        )
        self.assertEqual(r.status_code, 422, r.text)
        detail = r.json().get("detail")
        self.assertIsInstance(detail, list)
        self.assertTrue(len(detail) >= 1)

    def test_valid_post_returns_201(self) -> None:
        tg = 999_002
        self.create_user(telegram_user_id=tg)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": tg,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "Valid route notes for testing",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        self.assertIn("id", r.json())


if __name__ == "__main__":
    unittest.main()
