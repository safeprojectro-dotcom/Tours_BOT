from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.payment_webhook import PaymentWebhookParser, PaymentWebhookVerifier
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.payment import PaymentWebhookResponse
from app.services.payment_reconciliation import PaymentReconciliationService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhooks/{provider}", response_model=PaymentWebhookResponse)
async def payment_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PaymentWebhookResponse:
    raw_body = await request.body()
    settings = get_settings()
    verifier = PaymentWebhookVerifier(secret=settings.payment_webhook_secret)
    signature = request.headers.get("X-Payment-Signature")
    if not verifier.verify(raw_body=raw_body, signature=signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid payment signature")

    parser = PaymentWebhookParser()
    try:
        provider_result = parser.parse(provider=provider, raw_body=raw_body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    reconciliation = PaymentReconciliationService().reconcile_provider_result(
        db,
        provider_result=provider_result,
    )
    if reconciliation is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="payment session not found or payload mismatch",
        )

    db.commit()
    return PaymentWebhookResponse(
        status="processed",
        payment_id=reconciliation.payment.id,
        order_id=reconciliation.order.id,
        payment_status=reconciliation.payment.status,
        booking_status=reconciliation.order.booking_status,
        payment_confirmed=reconciliation.payment_confirmed,
        reconciliation_applied=reconciliation.reconciliation_applied,
    )
