from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class WaitlistEntry(CreatedAtMixin, Base):
    __tablename__ = "waitlist"
    __table_args__ = (
        UniqueConstraint("user_id", "tour_id", "status", name="uq_waitlist_user_tour_status"),
        CheckConstraint("seats_count > 0", name="ck_waitlist_seats_count_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True)
    seats_count: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    user: Mapped["User"] = relationship(back_populates="waitlist_entries")
    tour: Mapped["Tour"] = relationship(back_populates="waitlist_entries")
