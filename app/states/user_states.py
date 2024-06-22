from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    register = State()
    exchange_value_to_value = State()
    give_money = State()
    give_money_to_person = State()
    withdraw_money = State()
    add_money = State()
    substract_money = State()
