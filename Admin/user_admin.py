from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database

router = Router()


@router.callback_query(F.data == "ShowUsers")
async def see_users(callback: CallbackQuery, state: FSMContext):
    users_num = database.get_users_len()
    await state.set_data({"users_num": users_num})
    builder = InlineKeyboardBuilder()
    results = database.get_user_data_page(0)
    out_results = "Клиенты 1-{} из {}\n\n".format(len(results), users_num)
    for idx, trans in enumerate(results):
        idx += 1
        (
            user_id,
            first_name,
            last_name,
            level,
            cash_online,
            lucky,
            another_value,
            admin,
            registered_at,
        ) = trans
        builder.add(
            InlineKeyboardButton(text=str(idx), callback_data="User_" + str(user_id))
        )
        out_results += "{}. {} {} {}. Уровень: {}. Валюты: Cash: {}. Lucky: {}. Другая валюта: {}. Зарегистрирован: {}.\n".format(
            idx,
            "Админ." if admin else "",
            last_name,
            first_name,
            level,
            cash_online,
            lucky,
            another_value,
            registered_at,
        )
    builder.row(
        InlineKeyboardButton(text="⬅", callback_data="UsersPageChange_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="UsersPageChange_{}".format(
                1 if users_num < len(results) else 0
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("UsersPageChange_"))
async def see_users_change_page(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    page = int(callback.data.split("_")[1])
    await state.set_data(data)
    builder = InlineKeyboardBuilder()
    results = database.get_user_data_page(page)
    out_results = "Клиенты 1-{} из {}\n\n".format(len(results), data["users_num"])
    for idx, trans in enumerate(results):
        idx += 1
        (
            user_id,
            first_name,
            last_name,
            level,
            cash_online,
            lucky,
            another_value,
            admin,
            registered_at,
        ) = trans
        builder.add(
            InlineKeyboardButton(text=str(idx), callback_data="User_" + str(user_id))
        )
        out_results += "{}. {} {} {}. Уровень: {}. Валюты: Cash: {}. Lucky: {}. Другая валюта: {}. Зарегистрирован: {}.\n".format(
            idx,
            "Админ." if admin else "",
            last_name,
            first_name,
            level,
            cash_online,
            lucky,
            another_value,
            registered_at,
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="TransactionPageChange_{}".format(
                page - 1 if page != 0 else 0
            ),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                page + 1 if data["users_num"] < len(results) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("User_"))
async def see_user_detailed(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    id = callback.data.split("_")[1]
    builder.add(
        InlineKeyboardButton(
            text="Изменить имя и фамилию", callback_data="Change-Name-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить уровень", callback_data="Change-Level-%s" % id
        )
    )

    builder.add(
        InlineKeyboardButton(
            text="Поменять никнейм в телеграме", callback_data="Change-Username-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(text="Начислить Lucky", callback_data="Add-Lucky-%s" % id)
    )
    builder.add(
        InlineKeyboardButton(
            text="Начислить Cash Online", callback_data="Add-Cash_Online-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Начислить Другую валюту", callback_data="Add-Another_Value-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Снять Lucky", callback_data="Substract-Lucky-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Снять Cash Online", callback_data="Substract-Cash_Online-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Снять Другую валюту", callback_data="Substract-Another_Value-%s" % id
        )
    )
    data = database.get_user_xp_id_chat_id_name_level_username_money_admin_registered_referal_by_user_id(
        id
    )
    (
        xp,
        user_id,
        chat_id,
        first_name,
        last_name,
        level,
        username,
        cash_online,
        lucky,
        another_value,
        admin,
        registered_at,
        invited_from,
    ) = data
    if invited_from:
        invited_last_name, invited_first_name = database.get_name_by_user_id(
            invited_from
        )
    cur_limit = 50 + level * 25
    answer = """
{}ID пользователя: {}.
ID чата с ботом {}.
Имя фамилия: {} {}.
Никнейм в телеграме: @{}.
Уроовень: {} ({}/{}).
Монеты:
Lucky: {}.
Cash Online: {}.
Другая валюта: {}.
{}Зарегистрирован: {}.
""".format(
        (
            f"Реферал от {invited_last_name} {invited_first_name} id({invited_from})\n"
            if invited_from
            else ""
        ),
        user_id,
        chat_id,
        first_name,
        last_name,
        username,
        level,
        xp,
        cur_limit,
        lucky,
        cash_online,
        another_value,
        "Администратор.\n" if admin else "",
        registered_at,
    )
    if referals := database.get_user_id_name_by_invited_id(user_id):
        answer += "\nРефералы пользователя:"
        for referal in referals:
            referal_id, referal_last_name, referal_first_name = referal
            answer += f"\n{referal_last_name} {referal_first_name} {referal_id}"
    builder.adjust(2)
    await callback.message.answer(answer, reply_markup=builder.as_markup())
