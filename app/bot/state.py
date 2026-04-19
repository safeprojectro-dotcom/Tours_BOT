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
    choosing_service_composition = State()
    entering_fleet_summary = State()
