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
