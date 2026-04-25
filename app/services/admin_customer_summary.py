"""Build admin/ops customer summary from existing ``User`` fields (read-only, no external Telegram calls)."""

from __future__ import annotations

from app.models.user import User
from app.schemas.admin_customer_summary import AdminCustomerSummary


def _trim(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s or None


def derive_display_name(first_name: str | None, last_name: str | None) -> str | None:
    """As ADMIN_OPS_CUSTOMER_SUMMARY_GATE: first+last, else first, else last."""
    f = _trim(first_name)
    l = _trim(last_name)
    if f and l:
        return f"{f} {l}"
    if f:
        return f
    if l:
        return l
    return None


def normalize_username(username: str | None) -> str | None:
    u = _trim(username)
    if u is None:
        return None
    if u.startswith("@"):
        u = u[1:].strip()
    return u or None


def build_admin_customer_summary(
    *,
    telegram_user_id: int | None,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
) -> AdminCustomerSummary | None:
    """
    If ``telegram_user_id`` is None, return None (fail closed).
    Primary label is ``display_name`` when derivable, else ``tg:{id}``.
    Appends ``@username`` when present.
    """
    if telegram_user_id is None:
        return None
    disp = derive_display_name(first_name, last_name)
    u = normalize_username(username)
    if disp is not None:
        primary = disp
    else:
        primary = f"tg:{telegram_user_id}"
    if u:
        line = f"customer: {primary} @{u}"
    else:
        line = f"customer: {primary}"
    return AdminCustomerSummary(
        display_name=disp,
        username=u,
        summary_line=line,
    )


def build_admin_customer_summary_from_user(user: User | None) -> AdminCustomerSummary | None:
    if user is None:
        return None
    return build_admin_customer_summary(
        telegram_user_id=user.telegram_user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )
