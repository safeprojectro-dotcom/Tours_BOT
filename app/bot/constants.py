from __future__ import annotations

LANGUAGE_LABELS: dict[str, str] = {
    "en": "English",
    "ro": "Romana",
    "ru": "Russkiy",
    "sr": "Srpski",
    "hu": "Magyar",
    "it": "Italiano",
    "de": "Deutsch",
}

DEFAULT_PRIVATE_CATALOG_LIMIT = 3
PRIVATE_SOURCE_CHANNEL = "private"
START_TOUR_PREFIX = "tour_"
LANGUAGE_CALLBACK_PREFIX = "lang:"
TOUR_CALLBACK_PREFIX = "tour:"
BROWSE_TOURS_CALLBACK = "catalog:browse"
CHANGE_LANGUAGE_CALLBACK = "language:change"
FILTER_BY_DATE_CALLBACK = "catalog:filter:date"
FILTER_BY_DESTINATION_CALLBACK = "catalog:filter:destination"
FILTER_BY_BUDGET_CALLBACK = "catalog:filter:budget"
FILTER_DATE_CALLBACK_PREFIX = "catalog:date:"
FILTER_BUDGET_CALLBACK_PREFIX = "catalog:budget:"
CANCEL_DESTINATION_INPUT_CALLBACK = "catalog:destination:cancel"
PREPARE_RESERVATION_CALLBACK_PREFIX = "prepare:tour:"
PREPARE_SEAT_COUNT_CALLBACK_PREFIX = "prepare:seats:"
PREPARE_BOARDING_POINT_CALLBACK_PREFIX = "prepare:boarding:"
CHANGE_PREPARED_SEATS_CALLBACK = "prepare:change:seats"
CHANGE_PREPARED_BOARDING_CALLBACK = "prepare:change:boarding"
CREATE_TEMPORARY_RESERVATION_CALLBACK = "reservation:create:temporary"
REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX = "private:booking:assistance"
START_PAYMENT_ENTRY_CALLBACK_PREFIX = "payment:entry:"
BUDGET_OPTION_ANY = "any"
DATE_OPTION_WEEKEND = "weekend"
DATE_OPTION_NEXT_30_DAYS = "next30"
DATE_OPTION_ANY = "any"
MAX_PRIVATE_PREPARATION_SEATS = 6

CUSTOM_REQUEST_TYPE_CALLBACK_PREFIX = "crtype:"
CUSTOM_REQUEST_TYPE_GROUP = "crtype:group_trip"
CUSTOM_REQUEST_TYPE_ROUTE = "crtype:custom_route"
CUSTOM_REQUEST_TYPE_OTHER = "crtype:other"
CUSTOM_REQUEST_CANCEL_CALLBACK = "crtype:cancel"
