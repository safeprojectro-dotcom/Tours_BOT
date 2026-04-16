from enum import StrEnum

from sqlalchemy import Enum as SQLAlchemyEnum


class BookingStatus(StrEnum):
    NEW = "new"
    CUSTOMER_QUESTION = "customer_question"
    OPERATOR_QUESTION = "operator_question"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    READY_FOR_DEPARTURE = "ready_for_departure"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(StrEnum):
    UNPAID = "unpaid"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"


class CancellationStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_OPERATOR = "cancelled_by_operator"
    CANCELLED_NO_PAYMENT = "cancelled_no_payment"
    MOVED_TO_ANOTHER_DATE = "moved_to_another_date"
    MOVED_TO_ANOTHER_TOUR = "moved_to_another_tour"
    NO_SHOW = "no_show"
    DUPLICATE = "duplicate"


class TourStatus(StrEnum):
    DRAFT = "draft"
    OPEN_FOR_SALE = "open_for_sale"
    COLLECTING_GROUP = "collecting_group"
    GUARANTEED = "guaranteed"
    SALES_CLOSED = "sales_closed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class TourSalesMode(StrEnum):
    PER_SEAT = "per_seat"
    FULL_BUS = "full_bus"


def sqlalchemy_enum(enum_cls: type[StrEnum], *, name: str) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_cls,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
