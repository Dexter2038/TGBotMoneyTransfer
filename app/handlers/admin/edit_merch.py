from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states import AdminStates
from app.utils import database
from app.config import categories

import re
import os

router = Router(name="admin-edit-merch")


@router.callback_query(F.data.startswith("MerchChange_"))
async def merch_change_property(callback: CallbackQuery, state: FSMContext):
    # Photo, Category, Cost, Name, Description
    _, property, id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    match property:
        case "Photo":
            await callback.message.answer("Пришлите новое фото",
                                          reply_markup=builder.as_markup())
        case "Category":
            for category in categories:
                builder.add(
                    InlineKeyboardButton(
                        text=category,
                        callback_data=
                        f"MerchChangePropertyConfirm_{categories.index(category)}",
                    ))
            builder.adjust(1, 2)
            await callback.message.answer("Выберите новую категорию",
                                          reply_markup=builder.as_markup())
        case "Cost":
            await callback.message.answer("Введите новую цену",
                                          reply_markup=builder.as_markup())
        case "Name":
            await callback.message.answer("Введите новое название",
                                          reply_markup=builder.as_markup())
        case "Description":
            await callback.message.answer("Введите новое описание",
                                          reply_markup=builder.as_markup())
    await state.set_state(AdminStates.merch_change_property)
    await state.set_data({"property": property, "id": id})


@router.message(AdminStates.merch_change_property)
async def merch_change_property_enter(message: Message, state: FSMContext,
                                      bot: Bot):
    data = await state.get_data()
    property = data["property"]
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    match property:
        case "Photo":
            if not message.photo:
                await message.answer("Нужно прислать фото",
                                     reply_markup=builder.as_markup())
                await state.clear()
                return
            photo_id = message.photo[-1].file_id
            await bot.download(photo_id, "New_Merch_Photo.png")
        case "Cost":
            search = re.search(r"\d+", message.text)
            if not search:
                await message.answer(text="Нужно ввести число",
                                     reply_markup=builder.as_markup())
                await state.clear()
                return
            value = int(search.group())
            await state.set_data({"value": value, **data})
        case "Name":
            value = message.text
            await state.set_data({"value": value, **data})
        case "Description":
            value = message.text
            await state.set_data({"value": value, **data})
    builder.add(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data="MerchChangePropertyConfirm"))
    match property:
        case "Photo":
            await message.answer("Изменить фото?",
                                 reply_markup=builder.as_markup())
        case "Cost":
            await message.answer(f"Поменять цену на {value}?",
                                 reply_markup=builder.as_markup())
        case "Name":
            await message.answer(f"Поменять название на {value}?",
                                 reply_markup=builder.as_markup())
        case "Description":
            await message.answer(f"Поменять описание на {value}",
                                 reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("MerchChangePropertyConfirm"))
async def merch_change_property_confirm(callback: CallbackQuery,
                                        state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    match data["property"]:
        case "Photo":
            os.replace("New_Merch_Photo.png",
                       "merch_imgs/{}.png".format(data["id"]))
            photo = FSInputFile("merch_imgs/{}.png".format(data["id"]))
            await callback.message.answer_photo(
                photo,
                caption="Фото успешно изменено.",
                reply_markup=builder.as_markup(),
            )
        case "Category":
            category = callback.data.split("_")[1]
            database.set_merch_parameter_value_by_id("category", category,
                                                     data["id"])
            await callback.message.answer(
                f"Категория успешно изменена на {categories[int(category)]}",
                reply_markup=builder.as_markup(),
            )
        case "Cost":
            database.set_merch_parameter_value_by_id("cost", data["value"],
                                                     data["id"])
            await callback.message.answer(
                "Цена успешно изменена на {}".format(data["value"]),
                reply_markup=builder.as_markup(),
            )
        case "Name":
            database.set_merch_parameter_value_by_id("name", data["value"],
                                                     data["id"])
            await callback.message.answer(
                "Название успешно изменено на {}".format(data["value"]),
                reply_markup=builder.as_markup(),
            )
        case "Description":
            database.set_merch_parameter_value_by_id("description",
                                                     data["value"], data["id"])
            await callback.message.answer(
                "Описание успешно изменено на {}".format(data["value"]),
                reply_markup=builder.as_markup(),
            )
