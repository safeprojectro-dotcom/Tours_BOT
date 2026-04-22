from aiogram.fsm.state import State, StatesGroup


class PrivateEntryState(StatesGroup):
    choosing_language = State()
    entering_destination_preference = State()
    choosing_preparation_seat_count = State()
    choosing_preparation_boarding_point = State()
    reviewing_reservation_preparation = State()


class CustomRequestState(StatesGroup):
    """Layer C: structured custom trip / group request (Track 4)."""

    choosing_type = State()
    travel_dates = State()
    route_notes = State()
    group_size = State()
    special_conditions = State()


class SupplierOnboardingState(StatesGroup):
    """Y2.1: supplier Telegram onboarding (narrow v1 identity/access gate)."""

    entering_display_name = State()
    entering_contact_info = State()
    entering_region = State()
    choosing_legal_entity_type = State()
    entering_legal_registered_name = State()
    entering_legal_registration_code = State()
    entering_permit_license_type = State()
    entering_permit_license_number = State()
    choosing_service_composition = State()
    entering_fleet_summary = State()


class SupplierOfferIntakeState(StatesGroup):
    """Y2.2: supplier Telegram offer intake (draft + explicit moderation submit)."""

    entering_title = State()
    entering_description = State()
    entering_departure_point = State()
    entering_departure_datetime = State()
    entering_return_datetime = State()
    entering_seats_total = State()
    choosing_sales_mode = State()
    choosing_payment_mode = State()
    entering_base_price = State()
    entering_currency = State()
    entering_program_text = State()
    entering_vehicle_or_notes = State()
    awaiting_submit_action = State()


class AdminModerationState(StatesGroup):
    """Y28.1: Telegram admin moderation workspace state."""

    browsing_offer_queue = State()
    awaiting_reject_reason = State()


class AdminSupplierModerationState(StatesGroup):
    """Y29.3: Telegram admin supplier profile moderation workspace state."""

    browsing_supplier_queue = State()
    awaiting_reason = State()
