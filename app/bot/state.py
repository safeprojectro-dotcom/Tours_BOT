from aiogram.fsm.state import State, StatesGroup


class PrivateEntryState(StatesGroup):
    choosing_language = State()
    entering_destination_preference = State()
    choosing_preparation_seat_count = State()
    choosing_preparation_boarding_point = State()
    reviewing_reservation_preparation = State()
