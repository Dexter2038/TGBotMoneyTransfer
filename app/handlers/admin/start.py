from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils import database

router = Router(name="admin-start")


@router.message(Command("/admin"))
async def admin_enter(message: Message, state: FSMContext):
    data = database.get_admin_name_by_chat_id(message.chat.id)
    if not data:
        return
    last_name, first_name, admin = data
    if not admin:
        return
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Войти в панель админа",
                             callback_data="Admin"))
    await message.answer(
        f"Добро пожаловать, {last_name} {first_name}. Вы администатор.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "Admin")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not database.get_admin_by_chat_id(callback.message.chat.id):
        return
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Написать личное сообщение",
                             callback_data="WriteMessage"))
    builder.add(
        InlineKeyboardButton(text="Просмотреть пользователей",
                             callback_data="ShowUsers"))
    builder.add(
        InlineKeyboardButton(text="Просмотреть транзакции",
                             callback_data="ShowTransactionsAdmin"))
    builder.add(
        InlineKeyboardButton(text="Просмотреть мерч",
                             callback_data="ShowMerchAdmin"))
    builder.add(
        InlineKeyboardButton(text="Добавить предмет в мерч",
                             callback_data="AddMerchItem"))
    builder.add(
        InlineKeyboardButton(text="Просмотреть квизы",
                             callback_data="EditQuizzesAdmin"))
    builder.add(
        InlineKeyboardButton(text="Добавить категорию в мерч",
                             callback_data="AddMerchItemCategory"))
    builder.add(
        InlineKeyboardButton(text="Просмотреть не доставленный мерч",
                             callback_data="NotDeliveredMerch_0"))
    builder.add(
        InlineKeyboardButton(text="Просмотреть доставленный мерч",
                             callback_data="DeliveredMerch_0"))
    builder.add(
        InlineKeyboardButton(text="Изменить курс",
                             callback_data="ChangeCourse"))
    builder.add(
        InlineKeyboardButton(text="Сделать рассылку",
                             callback_data="StartMailing"))
    builder.add(
        InlineKeyboardButton(text="Добавить администратора",
                             callback_data="Addmin"))
    builder.add(
        InlineKeyboardButton(text="Снять администратора",
                             callback_data="SubAdmin"))
    builder.adjust(2)
    await callback.message.answer(
        f"Добро пожаловать, Баркалов Михаил.",
        reply_markup=builder.as_markup(),
    )
