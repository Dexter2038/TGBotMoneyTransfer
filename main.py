import asyncio
import logging
from os import getenv

from aiogram import Bot, F, Dispatcher, Router
from aiogram.types import (
    Message,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.token import TokenValidationError

import config, database


class UserStates(StatesGroup):
    register = State()
    exchange_value_to_value = State()
    give_money = State()
    give_money_to_person = State()
    withdraw_money = State()
    add_money = State()
    substract_money = State()


class AdminStates(StatesGroup):
    create_merch_photo = State()
    create_merch_name = State()
    create_merch_description = State()
    create_merch_cost = State()
    change_user_value = State()
    merch_change_property = State()
    add_quiz = State()
    add_merch_category = State()
    add_question_quiz = State()
    edit_question_question = State()
    edit_answer_question = State()
    edit_correct_answer_question = State()
    add_admin = State()
    substract_admin = State()
    change_course = State()
    mailing_link = State()
    set_sub_reward = State()
    set_ref_reward = State()
    write_message = State()
    write_message_to_user = State()


database.init()
config.init()

try:
    bot = Bot(token=getenv("tgBotToken"))

except TokenValidationError:
    logging.error("Неверный токен телеграм бота")
    exit(1)
except Exception:
    logging.error("Неизвестная ошибка при попытке запустить телеграм бота")
    exit(1)


dp = Dispatcher(bot=bot)
router = Router()

from Admin import (
    admin,
    change_user_value,
    mailing_admin,
    mailing_reward_admin,
    manage_admins,
    merch_add_admin,
    merch_add_category_admin,
    merch_admin,
    merch_edit,
    quiz_admin,
    scan_transaction_qr,
    transactions_admin,
    user_admin,
    user_money_admin,
    write_message_admin,
)


from User import user, transfer, transactions, quiz, merch, gifts, exchange, withdraw

dp.include_routers(
    user.router,
    withdraw.router,
    transfer.router,
    exchange.router,
    merch.router,
    gifts.router,
    transactions.router,
    admin.router,
    user_admin.router,
    change_user_value.router,
    user_money_admin.router,
    manage_admins.router,
    transactions_admin.router,
    write_message_admin.router,
    merch_admin.router,
    merch_add_admin.router,
    merch_edit.router,
    merch_add_category_admin.router,
    quiz_admin.router,
    mailing_admin.router,
    mailing_reward_admin.router,
    scan_transaction_qr.router,
    quiz.router,
)
database.create_withdraw_qr(0)

database.create_order(1, 400, 1)


@dp.message(Command("ref"))
async def ref(message: Message, state: FSMContext):
    link = await create_start_link(bot, str(message.from_user.username), encode=True)
    await message.answer(f"Ваша реферальная ссылка: {link}")


@dp.message(Command("start"))
async def start(message: Message, command: Command, state: FSMContext):
    if command:
        args = command.args
        if not args:
            return
        reference = decode_payload(args)
        if reference == message.from_user.username:
            return
        if database.get_user_id_by_chat_id(message.chat.id):
            return
        await state.set_data({"referal": reference})


@dp.message(UserStates.register)
async def register_user(message: Message, state: FSMContext):
    data = await state.get_data()
    if len(message.text.split(" ")) != 2:
        await state.set_data({**data})
        await message.answer("Введите пожалуйста ваше имя и фамилию через пробел")
        await state.set_state(UserStates.register)
        return
    if data.get("referal"):
        database.set_money_by_username("+", "invite", 1, data["referal"])
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    first_name, last_name = message.text.split(" ")
    if data.get("referal"):
        user_id = database.get_user_id_by_username(data["referal"])
        database.create_user(
            message.chat.id, first_name, last_name, message.from_user.username
        )
    else:
        database.create_user(
            message.chat.id, first_name, last_name, message.from_user.username
        )
    await message.answer(
        f"Вы успешно зарегистрированы, {last_name} {first_name}.",
        reply_markup=builder.as_markup(),
    )
    await state.clear()


@dp.message()
async def start(message: Message, state: FSMContext):
    result = database.get_name_by_chat_id(message.chat.id)
    if not result:
        data = await state.get_data()
        await state.set_data({**data})
        await state.set_state(UserStates.register)
        await message.answer(
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
    builder.adjust(1, 2)
    first_name, last_name = result
    await message.answer(
        f"Добрый день, {last_name} {first_name}!",
        reply_markup=builder.as_markup(),
    )


if __name__ == "__main__":
    el = asyncio.get_event_loop()
    el.run_until_complete(dp.start_polling(bot))
