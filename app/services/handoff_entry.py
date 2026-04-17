"""Minimal handoff persistence for support entry points (no operator notification yet)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.models.order import Order
from app.repositories.handoff import HandoffRepository


class HandoffEntryService:
    """Creates `handoffs` rows for MVP support signals; does not notify operators."""

    REASON_PRIVATE_CONTACT = "private_chat_contact"
    REASON_PRIVATE_HUMAN = "private_chat_human_request"
    REASON_GROUP_FOLLOWUP_START = "group_followup_start"
    REASON_MINI_APP_PREFIX = "mini_app_support"
    REASON_FULL_BUS_SALES_ASSISTANCE = "full_bus_sales_assistance"

    def __init__(
        self,
        *,
        handoff_repository: HandoffRepository | None = None,
    ) -> None:
        self._handoffs = handoff_repository or HandoffRepository()

    @staticmethod
    def _sanitize_reason_token(value: str, *, max_len: int) -> str:
        return (value or "").replace("|", "_").strip()[:max_len]

    @classmethod
    def build_full_bus_sales_assistance_reason(
        cls,
        *,
        tour_code: str,
        sales_mode: str,
        channel: str,
        screen_hint: str | None = None,
    ) -> str:
        """
        Compact structured reason for operator-assisted full-bus paths (Phase 7.1 / Step 5).

        Stored in ``handoffs.reason`` (varchar 255); no extra DB columns.
        """
        tc = cls._sanitize_reason_token(tour_code, max_len=64) or "unknown"
        sm = cls._sanitize_reason_token(sales_mode, max_len=24) or "full_bus"
        ch = cls._sanitize_reason_token(channel, max_len=24) or "unknown"
        parts = [
            cls.REASON_FULL_BUS_SALES_ASSISTANCE,
            f"tour={tc}",
            f"sales_mode={sm}",
            f"channel={ch}",
        ]
        if screen_hint:
            hint = cls._sanitize_reason_token(screen_hint.replace("|", " "), max_len=36)
            if hint:
                parts.append(f"hint={hint}")
        return "|".join(parts)[:255]

    @staticmethod
    def parse_full_bus_sales_assistance(reason: str) -> dict[str, str] | None:
        prefix = HandoffEntryService.REASON_FULL_BUS_SALES_ASSISTANCE
        if reason == prefix:
            return {"tour": "", "sales_mode": "", "channel": ""}
        if not reason.startswith(prefix + "|"):
            return None
        out: dict[str, str] = {}
        for part in reason.split("|")[1:]:
            if "=" not in part:
                continue
            key, _, val = part.partition("=")
            key, val = key.strip(), val.strip()
            if key:
                out[key] = val
        return out

    @staticmethod
    def is_full_bus_sales_assistance_reason(reason: str) -> bool:
        return HandoffEntryService.parse_full_bus_sales_assistance(reason) is not None

    def _user_sync(self) -> TelegramUserContextService:
        settings = get_settings()
        return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)

    def create_for_telegram_user(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        reason: str,
        order_id: int | None = None,
        priority: str = "normal",
        telegram_language_code: str | None = None,
        dedupe_open_by_reason: bool = False,
    ) -> int | None:
        """
        Persist a handoff row. Returns handoff id, or None if user could not be resolved
        or order ownership does not match.
        """
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=telegram_language_code,
        )
        if order_id is not None:
            order = session.get(Order, order_id)
            if order is None or order.user_id != user.id:
                return None

        safe_reason = (reason or "support")[:255]
        if dedupe_open_by_reason and order_id is None:
            existing = self._handoffs.find_open_by_user_reason(
                session,
                user_id=user.id,
                reason=safe_reason,
            )
            if existing is not None:
                return existing.id
        row = self._handoffs.create(
            session,
            data={
                "user_id": user.id,
                "order_id": order_id,
                "reason": safe_reason,
                "priority": priority[:32] if priority else "normal",
                "status": "open",
                "assigned_operator_id": None,
            },
        )
        return row.id

    def create_for_group_followup_start(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        telegram_language_code: str | None = None,
    ) -> int | None:
        """
        Persist a handoff for ``/start grp_followup`` (group → private follow-up chain).

        Dedupes open rows by (user, reason) to avoid duplicate open queue entries.
        """
        return self.create_for_telegram_user(
            session,
            telegram_user_id=telegram_user_id,
            reason=self.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            telegram_language_code=telegram_language_code,
            dedupe_open_by_reason=True,
        )

    def should_show_group_followup_resolved_confirmation(
        self,
        session: Session,
        *,
        user_id: int,
    ) -> bool:
        """
        Phase 7 / Step 16 — private ``grp_followup`` entry: show resolved copy when there is no
        open ``group_followup_start`` row and the latest such row is ``closed``.

        Read-only predicate; does not mutate. ``in_review`` or missing rows → False.
        """
        if (
            self._handoffs.find_open_by_user_reason(
                session,
                user_id=user_id,
                reason=self.REASON_GROUP_FOLLOWUP_START,
            )
            is not None
        ):
            return False
        latest = self._handoffs.find_latest_by_user_reason(
            session,
            user_id=user_id,
            reason=self.REASON_GROUP_FOLLOWUP_START,
        )
        if latest is None:
            return False
        return latest.status == "closed"

    def group_followup_private_intro_key(
        self,
        session: Session,
        *,
        user_id: int,
    ) -> str:
        """
        Map ``group_followup_start`` rows to a private intro key (Phase 7 follow-up UX; read-only).

        Aligns with admin read-side buckets from ``compute_group_followup_queue_state``:
        ``awaiting_assignment`` → pending; ``assigned_open`` → assigned; ``in_work`` → in_progress;
        ``resolved`` → resolved intro. Copy stays in ``app.bot.messages`` — no operator IDs or timing.
        """
        reason = self.REASON_GROUP_FOLLOWUP_START
        open_row = self._handoffs.find_open_by_user_reason(
            session,
            user_id=user_id,
            reason=reason,
        )
        if open_row is not None:
            if open_row.assigned_operator_id is not None:
                return "start_grp_followup_readiness_assigned"
            return "start_grp_followup_readiness_pending"

        latest = self._handoffs.find_latest_by_user_reason(
            session,
            user_id=user_id,
            reason=reason,
        )
        if latest is None:
            return "start_grp_followup_intro"
        if latest.status == "in_review":
            return "start_grp_followup_readiness_in_progress"
        if latest.status == "closed":
            return "start_grp_followup_resolved_intro"
        return "start_grp_followup_intro"
