"""Track 5c: pure helpers for RFQ bridge Mini App wiring (unit-testable without Flet)."""


def rfq_bridge_continue_to_payment_allowed(*, hold_active: bool, payment_entry_allowed: bool) -> bool:
    """Dominant CTA to Layer A payment-entry is allowed only when hold is valid and eligibility allows."""
    return bool(hold_active and payment_entry_allowed)
