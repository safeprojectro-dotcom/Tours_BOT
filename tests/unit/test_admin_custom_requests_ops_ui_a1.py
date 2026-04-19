"""A1: admin HTML operational console for Mode 3 custom requests (static shell + existing APIs)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class TestAdminCustomRequestsOpsUiA1:
    def test_ops_console_route_returns_html(self) -> None:
        app = create_app()
        client = TestClient(app)
        r = client.get("/admin/ui/custom-requests")
        assert r.status_code == 200
        assert "text/html" in (r.headers.get("content-type") or "")
        body = r.text.lower()
        assert "mode 3" in body
        assert "prepared" in body and "not proof" in body
        assert "v1" in body and "v4" in body
        assert "/admin/custom-requests" in r.text
        assert "needs attention only" in body
        assert "hide terminal" in body
        assert "customer continuation signals" in body
        assert "commercial and supplier progression context" in body
        assert "current operational decision" in body
        assert "blockers / waiting state" in body
        assert "not delivery evidence" in body
        assert "live workspace detail" in body
        assert "prev request" in body
        assert "next request" in body

    def test_ops_html_file_matches_router_path(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        html_path = repo_root / "app" / "admin" / "custom_requests_ops.html"
        assert html_path.is_file()
        raw = html_path.read_text(encoding="utf-8")
        assert "Prepared only" in raw or "prepared only" in raw.lower()
        assert "not_sent_to_customer_channels" in raw
        assert "operational scan" in raw.lower()
        assert "no payment readiness implied" in raw.lower()
        assert "listSearch" in raw
        assert "filterAttention" in raw
        assert "hideTerminal" in raw
        assert "operationalDecisionLabel" in raw
        assert "blockerSignals" in raw
        assert "derived from existing operational hints" in raw.lower()
        assert "updateWorkspaceSelectionMeta" in raw
        assert "navigateRelative" in raw
        assert "Current request #" in raw
