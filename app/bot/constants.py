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

SUPPLIER_ONBOARDING_CAPABILITY_CALLBACK_PREFIX = "supplier:onboarding:cap:"
SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_ONLY = "supplier:onboarding:cap:transport_only"
SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_GUIDE = "supplier:onboarding:cap:transport_guide"
SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_WATER = "supplier:onboarding:cap:transport_water"
SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_GUIDE_WATER = "supplier:onboarding:cap:transport_guide_water"
SUPPLIER_ONBOARDING_LEGAL_ENTITY_CALLBACK_PREFIX = "supplier:onboarding:legal_entity:"
SUPPLIER_ONBOARDING_LEGAL_ENTITY_COMPANY = "supplier:onboarding:legal_entity:company"
SUPPLIER_ONBOARDING_LEGAL_ENTITY_INDIVIDUAL_ENTREPRENEUR = "supplier:onboarding:legal_entity:individual_entrepreneur"
SUPPLIER_ONBOARDING_LEGAL_ENTITY_AUTHORIZED_CARRIER = "supplier:onboarding:legal_entity:authorized_carrier"

SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX = "supplier:offer:sales_mode:"
SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX = "supplier:offer:payment_mode:"
SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX = "supplier:offer:submit:"
SUPPLIER_OFFER_RESTART_CALLBACK = "supplier:offer:restart"
SUPPLIER_OFFER_NAV_CALLBACK_PREFIX = "supplier:offer:nav:"
SUPPLIER_OFFER_NAV_BACK_CALLBACK = "supplier:offer:nav:back"
SUPPLIER_OFFER_NAV_HOME_CALLBACK = "supplier:offer:nav:home"

ADMIN_OFFERS_ACTION_CALLBACK_PREFIX = "admin:offers:action:"
ADMIN_OFFERS_NAV_CALLBACK_PREFIX = "admin:offers:nav:"
ADMIN_OFFERS_ACTION_APPROVE = "admin:offers:action:approve"
ADMIN_OFFERS_ACTION_REJECT = "admin:offers:action:reject"
ADMIN_OFFERS_ACTION_PUBLISH = "admin:offers:action:publish"
ADMIN_OFFERS_ACTION_RETRACT = "admin:offers:action:retract"
ADMIN_OFFERS_NAV_NEXT = "admin:offers:nav:next"
ADMIN_OFFERS_NAV_PREV = "admin:offers:nav:prev"
ADMIN_OFFERS_NAV_BACK = "admin:offers:nav:back"
ADMIN_OFFERS_NAV_HOME = "admin:offers:nav:home"
