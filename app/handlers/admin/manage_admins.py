from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states import AdminStates
from app.utils import database

router = Router(name="admin-manage-admins")


@router.callback_query(F.data == "Addmin")
async def add_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Введите @никнейм пользователя в тг, чтобы добавить его в список администраторов"
    )
    await state.set_state(AdminStates.add_admin)


@router.message(AdminStates.add_admin)
async def add_admin_enter(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    username = message.text.split(" ")[0]
    data = database.get_user_id_name_admin_by_username(username)
    if not data:
        await message.answer(
            "Такой пользователь не найден.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    user_id, first_name, last_name, admin = data
    if admin:
        await message.answer(
            f"{last_name} {first_name} уже является администратором.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    builder.row(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data=f"AddminConfirm_{user_id}"))
    await message.answer(
        f"Вы хотите сделать пользователя {last_name, first_name} (id{user_id}) администратором?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("AddminConfirm_"))
async def add_admin_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    user_id = callback.data.split(" ")[1]
    data = database.get_username_name_admin_by_user_id(user_id)
    username, first_name, last_name, admin = data
    if admin:
        await callback.message.answer(
            f"{last_name} {first_name} уже является администратором.",
            reply_markup=builder.as_markup(),
        )
        return
    database.set_admin_status(1, user_id)
    await callback.message.answer(
        f"Вы успешно сделали пользователя @{username} {last_name, first_name} (id{user_id})  администратором?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "SubAdmin")
async def add_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Введите @никнейм пользователя в тг, чтобы снять его с поста администратора"
    )
    await state.set_state(AdminStates.substract_admin)


@router.message(AdminStates.substract_admin)
async def add_admin_enter(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    username = message.text.split(" ")[0]
    data = database.get_user_id_name_admin_by_username(username)
    if not data:
        await message.answer(
            "Такой пользователь не найден.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    user_id, first_name, last_name, admin = data
    if not admin:
        await message.answer(
            f"{last_name} {first_name} не является администратором.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    builder.row(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data=f"SubAdminConfirm_{user_id}"))
    await message.answer(
        f"Вы хотите снять пользователя {last_name, first_name} (id{user_id}) с поста администратора?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("SubAdminConfirm_"))
async def sub_admin_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    user_id = callback.data.split(" ")[1]
    data = database.get_username_name_admin_by_user_id(user_id)
    username, first_name, last_name, admin = data
    if not admin:
        await callback.message.answer(
            f"{last_name} {first_name} не является администратором.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    database.set_admin_status(0, user_id)
    await callback.message.answer(
        f"Вы успешно сняли пользователя @{username} {last_name, first_name} (id{user_id}) с поста администратора?",
        reply_markup=builder.as_markup(),
    )
