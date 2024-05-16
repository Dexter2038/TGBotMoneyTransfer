from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import UserStates
import database

router = Router()


@router.callback_query(F.data == "Profile")
async def profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    first_name, level, cash_online, lucky, xp, another_value = (
        database.get_profile_data_by_chat_id(callback.message.chat)
    )
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Главное меню", callback_data="MainMenu"))
    builder.add(
        InlineKeyboardButton(text="История транзакций", callback_data="Transactions")
    )
    builder.add(
        InlineKeyboardButton(text="Обменять монеты", callback_data="ExchangeMoney")
    )
    builder.add(InlineKeyboardButton(text="Передать монеты", callback_data="GiveMoney"))
    builder.add(
        InlineKeyboardButton(text="Вывести Cash Online", callback_data="WithdrawMoney")
    )
    builder.adjust(2)
    cur_limit = 50 + level * 25
    await callback.message.answer(
        f"""Здравствуйте, {first_name}.
Ваш уровень: {level} ({xp}/{cur_limit})
Баланс:
Lucky: {lucky}
CashOnline: {cash_online}
Другая валюта: {another_value}""",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "MainMenu")
async def start(callback: CallbackQuery, state: FSMContext):
    result = database.get_name_by_chat_id(callback.message.chat.id)
    if not result:
        data = await state.get_data()
        await state.set_data({**data})
        await state.set_state(UserStates.register)
        await callback.message.answer(
            "Здравствуйте. Вы не зарегистрированы. Напишите имя и фамилию через пробел."
        )
        return
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    builder.add(InlineKeyboardButton(text="Подарки", callback_data="Gifts"))
    builder.add(InlineKeyboardButton(text="Мерч", callback_data="ShowMerch"))
    builder.add(
        InlineKeyboardButton(text="Реферальная система", callback_data="ShowReferal")
    )
    builder.adjust(2)
    first_name, last_name = result
    await callback.message.answer(
        f"Добрый день, {last_name} {first_name}!",
        reply_markup=builder.as_markup(),
    )
