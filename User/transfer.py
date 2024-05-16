from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from main import UserStates, bot
from config import currencies

import re

router = Router()


@router.callback_query(F.data == "GiveMoney")
async def give(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    builder.row(InlineKeyboardButton(text="Lucky", callback_data="Give-Lucky"))
    builder.row(
        InlineKeyboardButton(text="Cash Online", callback_data="Give-Cash_Online")
    )
    builder.row(
        InlineKeyboardButton(text="Another Value", callback_data="Give-Another_Value")
    )
    await callback.message.answer(
        "Какую валюту Вы хотите передать?", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("Give-"))
async def give_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("-")[1]
    available = database.get_money_by_chat_id(
        currency.lower(), callback.message.chat.id
    )
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    await callback.message.answer(
        f"""
У Вас {available} {currency.replace("_"," ")}.
Сколько монет Вы хотите передать?""",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(UserStates.give_money)
    await state.set_data({"available": available, "currency": currency})


@router.message(UserStates.give_money)
async def give_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    result = int(search.group())
    if result > data["available"]:
        await message.answer(
            text=f"""
Недостаточно монет.
У вас {data["available"]} {data["currency"].replace("_", " ")}.
""",
            reply_markup=builder.as_markup(),
        )
        return
    await state.set_data({"amount": result, **data})
    await state.set_state(UserStates.give_money_to_person)
    await message.answer(
        text=f"""
Кому вы хотите перевести {result} {data["currency"].replace("_"," ")}?
Введите @username (указан в профиле)""",
        reply_markup=builder.as_markup(),
    )


@router.message(UserStates.give_money_to_person)
async def give_money_to_person(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    username = message.text.split(" ")[0]
    if username[0] == "@":
        username = username[1:]
    cur_data = database.get_user_name_user_id_by_username(username)
    if not cur_data:
        await message.answer(
            """
Такой пользователь не найден.
Введите имя пользователя.""",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    last_name, first_name, to_user_id = cur_data
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmGiveMoney")
    )
    await message.answer(
        f"""
Вы хотите передать {data["amount"]} {data["currency"].replace("_"," ")} пользователю {last_name} {first_name}?
    """,
        reply_markup=builder.as_markup(),
    )
    await state.set_data(
        {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "to_user_id": to_user_id,
            **data,
        }
    )


@router.callback_query(F.data == "ConfirmGiveMoney")
async def give_money_to_person_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    datum = database.get_money_user_id_by_chat_id(
        data["currency"].lower(), callback.message.chat.id
    )
    available, from_user_id = datum
    if available < data["amount"]:
        await callback.message.answer(
            """
У Вас недостаточно монет.
У Вас {available} {data["currency]}.""",
            reply_markup=builder.as_markup(),
        )
        await bot.answer_callback_query(callback.id, text="Недостаточно монет.")
        return
    database.set_money_by_chat_id(
        "-", data["currency"].lower(), data["amount"], callback.message.chat.id
    )
    database.set_money_by_username(
        "+", data["currency"].lower(), data["amount"], data["username"]
    )
    database.create_transaction_transfer(
        1,
        from_user_id,
        data["to_user_id"],
        data["amount"],
        currencies.index(data["currency"].replace("_", " ")),
    )
    await callback.message.answer(
        f"""Вы передали {data["amount"]} {data["currency"]} пользователю {data["last_name"]} {data["first_name"]}."""
    )
    await state.clear()
    await bot.answer_callback_query(callback.id, "Перевод прошел успешно.")
