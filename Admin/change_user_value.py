from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from main import AdminStates


import re

router = Router()


@router.callback_query(F.data.startswith("Change-"))
async def change_user_value(callback: CallbackQuery, state: FSMContext):
    _, change_value, id = callback.data.split("-")
    last_name, first_name, level, username = (
        database.get_user_name_level_username_by_user_id(id)
    )
    match change_value:
        case "Name":
            await callback.message.answer(
                "Введите имя и фамилию на которые хотите поменять имя и фамилию пользователя"
            )
        case "Level":
            await callback.message.answer(
                "Введите число уровня на которое хотите поменять уровень пользователя"
            )
        case "Username":
            await callback.message.answer(
                """
Введите @никнейм в телеграме, на который нужно поменять никнейм пользователя.
Нельзя менять этот параметр просто так, только в случае багов."""
            )
    await state.set_data(
        {
            "user_id": id,
            "change_value": change_value,
            "first_name": first_name,
            "last_name": last_name,
            "level": level,
            "username": username,
        }
    )
    await state.set_state(AdminStates.change_user_value)


@router.message(AdminStates.change_user_value)
async def enter_change_user_value(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    data = await state.get_data()
    match data["change_value"]:
        case "Name":
            if len(message.text.split(" ")) != 2:
                await message.answer("Введите имя и фамилию через пробел")
                return
            result = message.text.split(" ")
        case "Level":
            search = re.search("\d+", message.text)
            if not search:
                await message.answer(
                    text="Введите число", reply_markup=builder.as_markup()
                )
                return
            result = int(search.group())
        case "Username":
            result = message.text.split("")[0]
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmChangeUserValue")
    )
    match data["change_value"]:
        case "Name":
            first_name, last_name = result
            await message.answer(
                "Вы хотите поменять имя и фамилию пользователя {} {} на {} {}?".format(
                    data["first_name"], data["last_name"], first_name, last_name
                ),
                reply_markup=builder.as_markup(),
            )
        case "Level":
            await message.answer(
                "Вы хотите изменить уровень пользователя {} {} c {} на {}?".format(
                    data["last_name"], data["first_name"], data["level"], result
                ),
                reply_markup=builder.as_markup(),
            )
        case "Username":
            await message.answer(
                "Точно нужно изменить никнейм пользователя {} {} с {} на {}?".format(
                    data["last_name"], data["first_name"], data["username"], result
                ),
                reply_markup=builder.as_markup(),
            )
    await state.set_data({"result": result, **data})


@router.callback_query(F.data == "ConfirmChangeUserValue")
async def confirm_change_user_value(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    match data["change_value"]:
        case "Name":
            new_first_name, new_last_name = data["result"]
            database.set_user_name_by_user_id(
                new_first_name, new_last_name, data["user_id"]
            )
            await callback.message.answer(
                "Вы успешно сменили имя и фамилию пользователя с {} {} на {} {}.".format(
                    data["first_name"], data["last_name"], new_first_name, new_last_name
                )
            )
        case "Level":
            database.set_user_level_by_user_id(data["result"], data["user_id"])
            await callback.message.answer(
                "Вы успешно изменили уровень пользователя {} {} c {} на {}.".format(
                    data["last_name"], data["first_name"], data["level"], data["result"]
                )
            )
        case "Username":
            database.set_username_by_user_id(data["result"], data["user_id"])
            await callback.message.answer(
                "Вы успешно изменили никнейм пользователя {} {} с {} на {}.".format(
                    data["last_name"],
                    data["first_name"],
                    data["username"],
                    data["result"],
                )
            )
