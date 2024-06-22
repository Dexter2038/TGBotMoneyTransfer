from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states import AdminStates
from app.utils import database
from app.config import currencies
import re

router = Router(name="admin-manage-user-money")


@router.callback_query(F.data.startswith("Add-"))
async def add_money(callback: CallbackQuery, state: FSMContext):
    _, currency, id = callback.data.split("-")
    last_name, first_name = database.get_name_by_user_id(id)
    await callback.message.answer(
        "Введите, сколько {} Вы хотите начислить пользователю {} {}.".format(
            currency.replace("_", " "), last_name, first_name))
    await state.set_data({
        "user_id": id,
        "currency": currency.replace("_", " "),
        "first_name": first_name,
        "last_name": last_name,
    })
    await state.set_state(AdminStates.add_money)


@router.message(AdminStates.add_money)
async def enter_add_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    search = re.search(r"\d+", message.text)
    if not search:
        await message.answer(text="Введите число",
                             reply_markup=builder.as_markup())
        return
    amount = int(search.group())
    builder.row(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data="ConfirmAddMoney"))
    data = await state.get_data()
    await state.set_data({"amount": amount, **data})
    await message.answer(
        "Начислить {} {} клиенту {} {}?".format(amount, data["currency"],
                                                data["last_name"],
                                                data["first_name"]),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "ConfirmAddMoney")
async def confirm_add_money(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sql_currency = data["currency"].replace(" ", "_").lower()
    database.set_money_by_user_id("+", sql_currency, data["amount"],
                                  data["user_id"])
    admin_id = database.get_user_id_by_chat_id(callback.message.chat.id)
    database.create_transaction_transfer(4, admin_id, data["user_id"],
                                         data["amount"],
                                         currencies.index(data["currency"]))
    await callback.message.answer(
        "Вы успешно начислили {} {} пользователю {} {}".format(
            data["amount"], data["currency"], data["last_name"],
            data["first_name"]))


@router.callback_query(F.data.startswith("Substract-"))
async def substract_money(callback: CallbackQuery, state: FSMContext):
    _, currency, id = callback.data.split("-")
    last_name, first_name = database.get_name_by_user_id(id)
    await callback.message.answer(
        "Введите, сколько {} Вы хотите снять у пользователя {} {}.".format(
            currency.replace("_", " "), last_name, first_name))
    await state.set_data({
        "user_id": id,
        "currency": currency.replace("_", " "),
        "first_name": first_name,
        "last_name": last_name,
    })
    await state.set_state(AdminStates.substract_money)


@router.message(AdminStates.substract_money)
async def enter_substract_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    search = re.search(r"\d+", message.text)
    if not search:
        await message.answer(text="Введите число",
                             reply_markup=builder.as_markup())
        return
    amount = int(search.group())
    builder.row(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data="ConfirmSubstractMoney"))
    data = await state.get_data()
    await state.set_data({"amount": amount, **data})
    await message.answer(
        "Снять {} {} у клиента {} {}?".format(amount, data["currency"],
                                              data["last_name"],
                                              data["first_name"]),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "ConfirmSubstractMoney")
async def confirm_substract_money(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sql_currency = data["currency"].replace(" ", "_").lower()
    database.set_money_by_user_id("-", sql_currency, data["amount"],
                                  data["user_id"])
    admin_id = database.get_user_id_by_chat_id(callback.message.chat.id)
    database.create_transaction_transfer(5, admin_id, data["user_id"],
                                         data["amount"],
                                         currencies.index(data["currency"]))
    await callback.message.answer(
        "Вы успешно сняли {} {} у пользователя {} {}".format(
            data["amount"], data["currency"], data["last_name"],
            data["first_name"]))
