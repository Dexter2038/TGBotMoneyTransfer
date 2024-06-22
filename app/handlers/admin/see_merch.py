from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils import database
from app.config import categories

router = Router(name="admin-merch-watch")


@router.callback_query(F.data == "ShowMerchAdmin")
async def see_merch_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=category,
                callback_data=
                f"ShowMerchAdminCategory_{categories.index(category)}",
            ))
    builder.add(
        InlineKeyboardButton(text="Без категории",
                             callback_data="ShowMerchAdminNoCategory"))
    builder.add(
        InlineKeyboardButton(text="Добавить категорию",
                             callback_data="AddMerchItemCategory"))
    builder.adjust(1, 2)
    await callback.message.answer("Выберите категорию:",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("ShowMerchAdminCategory_"))
async def see_merch_admin_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(text="Выбрать другую категорию",
                             callback_data="ShowMerchAdmin"))
    category_number = int(callback.data.split("_")[1])
    category_size = int(database.get_merch_len(category_number))
    data = database.get_merch_item(category_number)
    try:
        id, name, description, cost = data
    except:
        await callback.message.answer("Категория пуста.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить фотографию",
                             callback_data=f"MerchChange_Photo_{id}"))
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer("Фотография пуста пуста.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить категорию",
                             callback_data=f"MerchChange_Category_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить цену",
                             callback_data=f"MerchChange_Cost_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить название",
                             callback_data=f"MerchChange_Name_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить описание",
                             callback_data=f"MerchChange_Description_{id}"))
    answer = f"""
Категория: {categories[category_number]}
Товар 1 из {category_size}

ID: {id}
Название: {name}
Цена: {cost} Lucky
Описание: {description}
    """
    builder.adjust(1, 1, 2)
    builder.row(
        InlineKeyboardButton(text="⬅",
                             callback_data="ShowMerchCategoryChange_1"),
        InlineKeyboardButton(
            text="➡",
            callback_data="ShowMerchAdminCategoryChange_{}".format(
                2 if category_size > 1 else 1),
        ),
    )
    await state.set_data({"category_number": category_number})
    await callback.message.answer_photo(photo=image,
                                        caption=answer,
                                        reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("ShowMerchCategoryChange_"))
async def see_merch_admin_category_change(callback: CallbackQuery,
                                          state: FSMContext):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(text="Выбрать другую категорию",
                             callback_data="ShowMerchAdmin"))
    data = await state.get_data()
    good_num = int(callback.data.split("_")[1])
    category_size = int(database.get_merch_len(data["category_number"]))
    datum = database.get_merch_item(data["category_number"], good_num - 1)
    try:
        id, name, description, cost = datum
    except:
        await callback.message.answer("Категория пуста.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить фотографию",
                             callback_data=f"MerchChange_Photo_{id}"))
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer("Фотография отсутствует.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить категорию",
                             callback_data=f"MerchChange_Category_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить цену",
                             callback_data=f"MerchChange_Cost_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить название",
                             callback_data=f"MerchChange_Name_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить описание",
                             callback_data=f"MerchChange_Description_{id}"))
    answer = f"""
Категория: {categories[data["category_number"]]}
Товар {good_num} из {category_size}

ID: {id}
Название: {name}
Цена: {cost} Lucky
Описание: {description}
    """
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data=
            f"ShowMerchAdminCategoryChange_{good_num - 1 if good_num != 0 else 1}",
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data=
            f"ShowMerchAdminCategoryChange_{good_num + 1 if category_size > good_num+1 else good_num}",
        ),
    )
    await state.set_data({"category_number": data["category_number"]})
    await callback.message.answer_photo(photo=image,
                                        caption=answer,
                                        reply_markup=builder.as_markup())


@router.callback_query(F.data == "ShowMerchAdminNoCategory")
async def see_merch_admin_no_category(callback: CallbackQuery,
                                      state: FSMContext):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(text="Выбрать другую категорию",
                             callback_data="ShowMerchAdmin"))
    size = int(database.get_merch_len())
    data = database.get_merch_item()
    try:
        id, name, description, cost, category = data
    except:
        await callback.message.answer("Мерч пуст.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить фотографию",
                             callback_data=f"MerchChange_Photo_{id}"))
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer("Фотография пуста пуста.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить категорию",
                             callback_data=f"MerchChange_Category_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить цену",
                             callback_data=f"MerchChange_Cost_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить название",
                             callback_data=f"MerchChange_Name_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить описание",
                             callback_data=f"MerchChange_Description_{id}"))
    answer = f"""
Товар 1 из {size}

ID: {id}
Категория: {categories[category]}
Название: {name}
Цена: {cost} Lucky
Описание: {description}
    """
    builder.adjust(1, 1, 2)
    builder.row(
        InlineKeyboardButton(text="⬅",
                             callback_data="ShowMerchNoCategoryChange_1"),
        InlineKeyboardButton(
            text="➡",
            callback_data="ShowMerchAdminNoCategoryChange_{}".format(
                2 if size > 1 else 1),
        ),
    )
    await callback.message.answer_photo(photo=image,
                                        caption=answer,
                                        reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("ShowMerchNoCategoryChange_"))
async def see_merch_admin_no_category_change(callback: CallbackQuery,
                                             state: FSMContext):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(text="Выбрать другую категорию",
                             callback_data="ShowMerchAdmin"))
    good_num = int(callback.data.split("_")[1])
    size = int(database.get_merch_len())
    data = database.get_merch_item(offset=good_num - 1)
    try:
        id, name, description, cost, category = data
    except:
        await callback.message.answer("Мерч пуст.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить фотографию",
                             callback_data=f"MerchChange_Photo_{id}"))
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer("Фотография отсутствует.",
                                      reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(text="Изменить категорию",
                             callback_data=f"MerchChange_Category_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить цену",
                             callback_data=f"MerchChange_Cost_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить название",
                             callback_data=f"MerchChange_Name_{id}"))
    builder.add(
        InlineKeyboardButton(text="Изменить описание",
                             callback_data=f"MerchChange_Description_{id}"))
    answer = f"""
Товар {good_num} из {size}

ID: {id}
Категория: {categories[category]}
Название: {name}
Цена: {cost} Lucky
Описание: {description}
    """
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data=
            f"ShowMerchAdminNoCategoryChange_{good_num - 1 if good_num != 0 else 1}",
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data=
            f"ShowMerchAdminNoCategoryChange_{good_num + 1 if size > good_num+1 else good_num}",
        ),
    )
    await callback.message.answer_photo(photo=image,
                                        caption=answer,
                                        reply_markup=builder.as_markup())
