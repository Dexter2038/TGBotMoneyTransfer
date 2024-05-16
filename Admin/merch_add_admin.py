from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from main import AdminStates, bot
from config import categories

import re
import os

router = Router()


@router.callback_query(F.data == "AddMerchItem")
async def add_merch_item_category(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=category,
                callback_data=f"AddMerchItemCategory_{categories.index(category)}",
            )
        )
    builder.add(
        InlineKeyboardButton(
            text="Добавить категорию", callback_data="AddMerchItemCategory"
        )
    )
    builder.adjust(1, 2)
    await callback.message.answer(
        "Выберите категорию: ", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("AddMerchItemCategory_"))
async def add_merch_item_name(callback: CallbackQuery, state: FSMContext):
    category_number = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Напишите название товара", reply_markup=builder.as_markup()
    )
    await state.set_data({"category_number": category_number})
    await state.set_state(AdminStates.create_merch_name)


@router.message(AdminStates.create_merch_name)
async def add_merch_item_cost(message: Message, state: FSMContext):
    data = await state.get_data()
    name = message.text
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await message.answer("Напишите цену товара", reply_markup=builder.as_markup())
    await state.set_data({"name": name, **data})
    await state.set_state(AdminStates.create_merch_cost)


@router.message(AdminStates.create_merch_cost)
async def add_merch_item_description(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    data = await state.get_data()
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    cost = int(search.group())
    await message.answer("Напишите описание товара", reply_markup=builder.as_markup())
    await state.set_data({"cost": cost, **data})
    await state.set_state(AdminStates.create_merch_description)


@router.message(AdminStates.create_merch_description)
async def add_merch_item_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    description = message.text
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await message.answer(
        "Пришлите фотографию для витрины", reply_markup=builder.as_markup()
    )
    await state.set_data({"description": description, **data})
    await state.set_state(AdminStates.create_merch_photo)


@router.message(F.photo and AdminStates.create_merch_photo)
async def add_merch_item_photo_confirm(message: Message, state: FSMContext):
    if not message.photo:
        return
    photo_id = message.photo[-1].file_id
    await bot.download(photo_id, "Merch_Item_Photo.png")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="AddMerchItemConfirm")
    )
    data = await state.get_data()
    photo = FSInputFile("Merch_Item_Photo.png")
    await message.answer_photo(
        photo,
        f"""
Вот так будет выглядеть товар, выкладывать?

Категория: {categories[int(data["category_number"])]}
Товар x из x


Название: {data["name"]}
Цена: {data["cost"]} Lucky
Описание: {data["description"]}""",
        reply_markup=builder.as_markup(),
    )
    await state.set_data({**data})


@router.callback_query(F.data == "AddMerchItemConfirm")
async def add_merch_item_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        return
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    datum = database.get_last_merch_id()
    last_id = 1 if datum is None else datum[0]
    database.create_merch(
        data["name"], data["category_number"], data["description"], data["cost"]
    )
    os.replace("Merch_Item_Photo.png", f"merch_imgs/{last_id}.png")
    await callback.message.answer(
        "Успешно добавлен товар {} за {}".format(data["name"], data["cost"]),
        reply_markup=builder.as_markup(),
    )
