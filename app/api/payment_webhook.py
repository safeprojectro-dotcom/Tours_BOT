from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping

from app.models.enums import PaymentStatus
from app.schemas.payment import PaymentProviderResult, PaymentWebhookPayload


class PaymentWebhookVerifier:
    def __init__(self, *, secret: str | None) -> None:
        self.secret = secret

    def verify(self, *, raw_body: bytes, signature: str | None) -> bool:
        if not self.secret or not signature:
            return False
        expected = hmac.new(self.secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


class PaymentWebhookParser:
    PAID_STATUSES = {"paid", "success", "succeeded"}
    PENDING_STATUSES = {"pending", "processing", "awaiting_payment"}
    UNPAID_STATUSES = {"failed", "unpaid", "expired", "cancelled", "canceled"}

    def parse(self, *, provider: str, raw_body: bytes) -> PaymentProviderResult:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise ValueError("invalid payment webhook payload") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("invalid payment webhook payload")

        webhook_payload = PaymentWebhookPayload.model_validate(payload)
        return PaymentProviderResult(
            provider=provider,
            external_payment_id=webhook_payload.external_payment_id,
            verified=True,
            provider_status=webhook_payload.status,
            normalized_status=self._normalize_status(webhook_payload.status),
            amount=webhook_payload.amount,
            currency=webhook_payload.currency,
            raw_payload=webhook_payload.payload or dict(payload),
        )

    def _normalize_status(self, status: str) -> PaymentStatus:
        normalized = status.strip().lower()
        if normalized in self.PAID_STATUSES:
            return PaymentStatus.PAID
        if normalized in self.PENDING_STATUSES:
            return PaymentStatus.AWAITING_PAYMENT
        if normalized in self.UNPAID_STATUSES:
            return PaymentStatus.UNPAID
        raise ValueError("unsupported payment status")
