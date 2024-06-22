from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.deep_linking import decode_payload, create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states import UserStates
from app.utils import database

router = Router(name="user-start")


@router.callback_query(F.data == "Profile")
async def profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    first_name, level, cash_online, lucky, xp, another_value = (
        database.get_profile_data_by_chat_id(callback.message.chat.id))
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Главное меню", callback_data="MainMenu"))
    builder.add(
        InlineKeyboardButton(text="История транзакций",
                             callback_data="Transactions"))
    builder.add(
        InlineKeyboardButton(text="Обменять монеты",
                             callback_data="ExchangeMoney"))
    builder.add(
        InlineKeyboardButton(text="Передать монеты",
                             callback_data="GiveMoney"))
    builder.add(
        InlineKeyboardButton(text="Вывести Cash Online",
                             callback_data="WithdrawMoney"))
    builder.adjust(2)
    cur_limit = 50 + level * 25
    await callback.message.answer(
        f"""Здравствуйте, {first_name}.
Ваш уровень: {level} ({xp}/{cur_limit})
Баланс:
Lucky: {lucky}
CashOnline: {cash_online}
E Coin: {another_value}""",
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
        InlineKeyboardButton(text="Реферальная система",
                             callback_data="ShowReferal"))
    builder.adjust(2)
    first_name, last_name = result
    await callback.message.answer(
        f"Добрый день, {last_name} {first_name}!",
        reply_markup=builder.as_markup(),
    )


@router.message(Command("start"))
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


@router.message(UserStates.register)
async def register_user(message: Message, state: FSMContext):
    data = await state.get_data()
    if len(message.text.split(" ")) != 2:
        await state.set_data({**data})
        await message.answer(
            "Введите пожалуйста ваше имя и фамилию через пробел")
        await state.set_state(UserStates.register)
        return
    if data.get("referal"):
        database.set_money_by_username("+", "invite", 1, data["referal"])
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    first_name, last_name = message.text.split(" ")
    if data.get("referal"):
        user_id = database.get_user_id_by_username(data["referal"])
        database.create_user(message.chat.id, first_name, last_name,
                             message.from_user.username)
    else:
        database.create_user(message.chat.id, first_name, last_name,
                             message.from_user.username)
    await message.answer(
        f"Вы успешно зарегистрированы, {last_name} {first_name}.",
        reply_markup=builder.as_markup(),
    )
    await state.clear()


@router.message(Command("ref"))
async def ref(message: Message, state: FSMContext, bot: Bot):
    link = await create_start_link(bot,
                                   str(message.from_user.username),
                                   encode=True)
    await message.answer(f"Ваша реферальная ссылка: {link}")


@router.message()
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
        InlineKeyboardButton(text="Реферальная система",
                             callback_data="ShowReferal"))
    builder.adjust(1, 2)
    first_name, last_name = result
    await message.answer(
        f"Добрый день, {last_name} {first_name}!",
        reply_markup=builder.as_markup(),
    )
