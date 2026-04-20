"""ORM model imports for SQLAlchemy metadata registration."""

from app.models.custom_marketplace_request import CustomMarketplaceRequest, SupplierCustomRequestResponse
from app.models.custom_request_booking_bridge import CustomRequestBookingBridge
from app.models.content_item import ContentItem
from app.models.handoff import Handoff
from app.models.knowledge_base import KnowledgeBaseEntry
from app.models.message import Message
from app.models.notification_outbox import NotificationOutbox
from app.models.order import Order
from app.models.payment import Payment
from app.models.tour import BoardingPoint, BoardingPointTranslation, Tour, TourTranslation
from app.models.user import User
from app.models.supplier import Supplier, SupplierApiCredential, SupplierOffer, SupplierOfferExecutionLink
from app.models.waitlist import WaitlistEntry

__all__ = [
    "CustomMarketplaceRequest",
    "CustomRequestBookingBridge",
    "BoardingPoint",
    "BoardingPointTranslation",
    "ContentItem",
    "Handoff",
    "KnowledgeBaseEntry",
    "Message",
    "NotificationOutbox",
    "Order",
    "Payment",
    "Supplier",
    "SupplierApiCredential",
    "SupplierCustomRequestResponse",
    "SupplierOffer",
    "SupplierOfferExecutionLink",
    "Tour",
    "TourTranslation",
    "User",
    "WaitlistEntry",
]
