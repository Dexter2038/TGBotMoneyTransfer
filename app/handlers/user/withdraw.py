from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states import UserStates
from app.utils import database

import segno
import re

router = Router(name="user-withdraw")


@router.callback_query(F.data == "WithdrawMoney")
async def withdraw_money(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль",
                             callback_data="Profile"))
    available = database.get_money_by_chat_id("cash_online",
                                              callback.message.chat.id)
    await callback.message.answer(
        f"""
У Вас {available} Cash Online монет.
Введите, сколько монет вы хотити вывести.
    """,
        reply_markup=builder.as_markup(),
    )
    await state.set_state(UserStates.withdraw_money)
    await state.set_data({"available": available})


@router.message(UserStates.withdraw_money)
async def enter_withdraw_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    search = re.search(r"\d+", message.text)
    if not search:
        await message.answer(text="Введите число",
                             reply_markup=builder.as_markup())
        return
    result = int(search.group())
    if result > data["available"]:
        await message.answer(
            text=f"""
Недостаточно монет.
У вас {data["available"]} Cash Online.
""",
            reply_markup=builder.as_markup(),
        )
        return
    builder.row(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data="ConfirmWithdrawMoney"))
    await state.set_data({"amount": result})
    await message.answer(
        f"""
Вы хотите вывести {result} Cash Online?
    """,
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "ConfirmWithdrawMoney")
async def confirm_withdraw_money(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = database.get_user_id_by_chat_id(callback.message.chat.id)
    id = database.get_last_qr_id + 1
    database.create_withdraw_qr(data["amount"])
    message = '{"type" : "withdraw","qr_id" : %s,"amount" : %s,"user_id" : %s}' % (
        id,
        data["amount"],
        user_id,
    )
    qr = segno.make_qr(message)
    qr.save("QR.png", scale=15)
    qr = FSInputFile("QR.png")
    await callback.message.answer_photo(
        qr,
        """
Предъявите QRCode нашему сотруднику.
Он его отсканирует.""",
    )
