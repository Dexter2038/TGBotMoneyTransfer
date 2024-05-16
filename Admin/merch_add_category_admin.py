from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import AdminStates
from config import categories

router = Router()


@router.callback_query(F.data == "AddMerchItemCategory")
async def add_merch_category(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(
            text="Подтвердить", callback_data="AddMerchItemCategoryConfirm"
        )
    )
    await callback.message.answer(
        "Вы точно хотите добавить новую категорию?", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "AddMerchItemCategoryConfirm")
async def add_merch_category_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(
            text="Точно уверен!", callback_data="AddMerchItemCategoryConfirmConfirm"
        )
    )
    await callback.message.answer(
        "Вы точно уверены, что хотите добавить новую категорию? Удалить обратно её будет нельзя!",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "AddMerchItemCategoryConfirmConfirm")
async def add_merch_category_confirm_confirm(
    callback: CallbackQuery, state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(
            text="ТОЧНО УВЕРЕН!",
            callback_data="AddMerchCategoryItemConfirmConfirmConfirm",
        )
    )
    await callback.message.answer(
        "Убрать обратно её будет нельзя!", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "AddMerchCategoryItemConfirmConfirmConfirm")
async def add_merch_category_confirm_confirm_confirm(
    callback: CallbackQuery, state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Хорошо, введите название новой категории.", reply_markup=builder.as_markup()
    )
    await state.set_state(AdminStates.add_merch_category)


@router.message(AdminStates.add_merch_category)
async def add_merch_category_enter(message: Message, state: FSMContext):
    new_category = message.text
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(text="Да, это так", callback_data="AddMerchCategory")
    )
    await state.set_data({"category": new_category})
    await message.answer(
        f"Ваша категория: {new_category}. Вы точно хотите её добавить?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "AddMerchCategory")
async def add_merch_category_enter_confirm(callback: CallbackQuery, state: FSMContext):
    new_category = (await state.get_data())["category"]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(
            text="Да, это моя категория, я хочу её добавить!",
            callback_data="AddMerchCategoryConfirm",
        )
    )
    await callback.message.answer(
        f"Это ваша категория: {new_category}. Вы уверены, что точно хотите её добавить? Это последнее предупреждение. Если точно уверены, что хотите добавить эту категорию, не нажимайте перед этим никаких других кнопок и не пишите сообщений.",
        reply_markup=builder.as_markup(),
    )
    await state.clear()
    await state.set_data({"category": new_category})


@router.callback_query(F.data == "AddMerchCategoryConfirm")
async def add_merch_category_total_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    new_category = await state.get_data()
    new_category = new_category["category"]
    categories.append(new_category)
    with open("categories.txt", "w") as f:
        f.write("")
    with open("categories.txt", "a", encoding="utf-8") as f:
        for category in categories:
            f.write(category + "\n")
    await callback.message.answer(
        f"Вы успешно добавили категорию {new_category}!",
        reply_markup=builder.as_markup(),
    )
