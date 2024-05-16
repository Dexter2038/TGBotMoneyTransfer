from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from main import AdminStates, bot

router = Router()


@router.callback_query(F.data == "WriteMessage")
async def write_message(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        text="Введите @никнейм пользователя, его id (можно узнать в 'посмотреть пользователей')\nили его имя и фамилию"
    )
    await state.set_state(AdminStates.write_message)


@router.message(AdminStates.write_message)
async def write_message_enter(message: Message, state: FSMContext):
    if len(message.text.split(" ")) > 2:
        return
    if len(message.text.split(" ")) == 2:
        first_name, last_name = message.text.split(" ")
        chat_id = database.get_chat_id_by_names(first_name, last_name)
        if chat_id := database.get_chat_id_by_names(first_name, last_name):
            await message.answer(
                f"Введите сообщение, которое вы хотите отправить пользователю {last_name} {first_name}"
            )
            await state.set_state(AdminStates.write_message_to_user)
            await state.set_data({"chat_id": chat_id})
        else:
            await message.answer(f"Пользователь '{first_name} {last_name}' не найден")
        return  # Имя фамилия
    if message.text[0] == "@":
        username = message.text[1:]
        if chat_id := database.get_chat_id_by_username(username):
            await message.answer(
                f"Введите сообщение, которое вы хотите отправить пользователю с никнеймом {username}"
            )
            await state.set_state(AdminStates.write_message_to_user)
            await state.set_data({"chat_id": chat_id})
        else:
            await message.answer(f"Пользователь с никнеймом {username} не найден")
        return  # Никнейм
    if message.text.isdigit():
        id = message.text
        chat_id = database.get_chat_id_by_user_id(id)
        if chat_id := database.get_chat_id_by_user_id(id):
            await message.answer(
                f"Введите сообщение, которое вы хотите отправить пользователю c id{id}"
            )
            await state.set_state(AdminStates.write_message_to_user)
            await state.set_data({"chat_id": chat_id})
        else:
            await message.answer(f"Пользователь c id{id} не найден")
        return  # ID


@router.message(AdminStates.write_message_to_user)
async def write_message_to_user(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data=f"WriteMessageConfirm")
    )
    await message.answer(
        f"Вы хотите отправить пользователю сообщение: '{message.text}'?",
        reply_markup=builder.as_markup(),
    )
    await state.update_data({"text": message.text})


@router.callback_query(F.data == "WriteMessageConfirm")
async def write_message_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    data = await state.get_data()
    await bot.send_message(data["chat_id"], data["text"])
    await callback.message.answer(
        "Сообщение успешно отправлено пользователю", reply_markup=builder.as_markup()
    )
