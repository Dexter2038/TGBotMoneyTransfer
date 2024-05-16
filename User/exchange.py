from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from config import course, convert_value, currencies
from main import UserStates, bot
import re

router = Router()


@router.callback_query(F.data == "ExchangeMoney")
async def exchange_money(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Lucky на Cash Online",
            callback_data="Exchange-LuckyToCash_Online",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Cash Online на Lucky",
            callback_data="Exchange-Cash_OnlineToLucky",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Lucky на Another Value",
            callback_data="Exchange-LuckyToAnother_Value",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Another Value на Lucky",
            callback_data="Exchange-Another_ValueToLucky",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Cash Online на Another Value",
            callback_data="Exchange-Cash_OnlineToAnother_Value",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Another Value на Cash Online",
            callback_data="Exchange-Another_ValueToCash_Online",
        )
    )
    await callback.message.answer(
        "Какую валюту на какую вы хотиsте обменять?", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("Exchange-"))
async def exchange_value_to_value(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="ExchangeMoney"))
    currencyes = callback.data.split("-")[1].split("To")
    availables = database.get_two_money_values_by_chat_id(callback.message.chat.id)
    first_available, second_available = availables
    first, second = map(lambda x: x.replace("_", " "), currencyes)
    response = f"""
У вас {first_available} {first} и {second_available} {second}.
Курс: {course[first]} {first} = {course[second]} {second}."""
    if course[first] > course[second]:
        response += """
Напишите, сколько монет вы хотите получить.
"""
        await state.set_data(
            {
                "transfer": "to",
                "first": first,
                "second": second,
                "first_available": first_available,
                "first_currency": currencyes[0].lower(),
                "second_currency": currencyes[1].lower(),
            }
        )
    else:
        response += f"""
Напишите, сколько монет вы хотите обменять на {second}.
"""
        await state.set_data(
            {
                "transfer": "from",
                "first": first,
                "second": second,
                "first_available": first_available,
                "first_currency": currencyes[0].lower(),
                "second_currency": currencyes[1].lower(),
            }
        )
    await state.set_state(UserStates.exchange_value_to_value)
    await callback.message.answer(text=response, reply_markup=builder.as_markup())


@router.message(UserStates.exchange_value_to_value)
async def enter_exchange_value_to_value(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="ExchangeMoney"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    result = int(search.group())
    data = await state.get_data()
    await state.clear()
    needed = (
        convert_value(result, data["second"], data["first"])
        if data["transfer"] == "to"
        else result
    )
    if data["first_available"] < needed:
        await message.answer(
            f"""
У вас недостаточно монет.
У вас {data["first_available"]} {data["first"]}.
""",
            reply_markup=builder.as_markup(),
        )
        return
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmExchangeValue")
    )
    out = convert_value(needed, data["first"], data["second"])
    await state.set_data(
        {
            "available": data["first_available"],
            "needed": needed,
            "out": out,
            "needed_currency": data["first"],
            "out_currency": data["second"],
        }
    )
    await message.answer(
        text=f"""Вы хотите обменять {needed} {data["first"]} на {out} {data["second"]}?""",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "ConfirmExchangeValue")
async def confirm_exchange_value_to_value(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Вернуться", callback_data="ExchangeMoney"))
    data = await state.get_data()
    datum = database.get_money_user_id_by_chat_id(
        data["needed_currency"].lower().replace(" ", "_"), callback.message.chat.id
    )
    available, user_id = datum
    if available < data["needed"]:
        await callback.message.answer(
            f"""
У вас недостаточно монет.
У вас {available} {data["needed_currency"]}""",
            reply_markup=builder.as_markup(),
        )
        await bot.answer_callback_query(callback.id, text="Недостаточно монет.")
        return
    database.set_money_by_chat_id(
        "-", data["needed_currency"], data["needed"], callback.message.chat.id
    )
    database.set_money_by_chat_id(
        "+", data["out_currency"], data["out"], callback.message.chat.id
    )
    database.create_transaction_exchange(
        0,
        user_id,
        data["needed"],
        currencies.index(data["needed_currency"]),
        data["out"],
        currencies.index(data["out_currency"]),
    )
    await callback.message.answer(
        f"""Вы обменяли {data["needed"]} {data["needed_currency"]} на {data["out"]} {data["out_currency"]}."""
    )
    await bot.answer_callback_query(callback.id, "Обмен валют прошел успешно.")
