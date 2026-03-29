from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    home_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user",
        foreign_keys="Order.user_id",
    )
    assigned_orders: Mapped[list["Order"]] = relationship(
        back_populates="assigned_operator",
        foreign_keys="Order.assigned_operator_id",
    )
    handoffs: Mapped[list["Handoff"]] = relationship(
        back_populates="user",
        foreign_keys="Handoff.user_id",
    )
    assigned_handoffs: Mapped[list["Handoff"]] = relationship(
        back_populates="assigned_operator",
        foreign_keys="Handoff.assigned_operator_id",
    )
    waitlist_entries: Mapped[list["WaitlistEntry"]] = relationship(back_populates="user")
    messages: Mapped[list["Message"]] = relationship(back_populates="user")
    approved_content_items: Mapped[list["ContentItem"]] = relationship(back_populates="approver")
