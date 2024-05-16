from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from config import categories

router = Router()


@router.callback_query(F.data == "ShowMerch")
async def merch(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=category,
                callback_data=f"ShowMerchCategory_{categories.index(category)}",
            )
        )
    builder.adjust(1, 2)
    await callback.message.answer(
        "Выберите категорию:", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("ShowMerchCategory_"))
async def merch_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(
        *(
            InlineKeyboardButton(text="Профиль", callback_data="Profile"),
            InlineKeyboardButton(
                text="Выбрать другую категорию", callback_data="ShowMerch"
            ),
        )
    )
    category_number = int(callback.data.split("_")[1])
    category_size = int(database.get_merch_len(category_number))
    data = database.get_merch_item(category_number, 0)
    try:
        id, name, description, cost = data
    except:
        await callback.message.answer(
            "Категория пуста.", reply_markup=builder.as_markup()
        )
        return
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer(
            "Категория пуста.", reply_markup=builder.as_markup()
        )
        return
    answer = f"""
Категория: {categories[category_number]}
Товар 1 из {category_size}

Название: {name}
Цена: {cost} Lucky
Описание: {description}
    """
    builder.row(InlineKeyboardButton(text="Купить", callback_data=f"BuyMerch_{id}"))
    builder.row(
        InlineKeyboardButton(text="⬅", callback_data="ShowMerchChange_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="ShowMerchChange_{}".format(2 if category_size > 1 else 0),
        ),
    )
    await state.set_data({"category_number": category_number})
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("ShowMerchChange_"))
async def merch_category_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(
        (
            InlineKeyboardButton(text="Профиль", callback_data="Profile"),
            InlineKeyboardButton(
                text="Выбрать другую категорию", callback_data="ShowMerch"
            ),
        )
    )
    data = await state.get_data()
    good_num = int(callback.data.split("_")[1])
    category_size = int(database.get_merch_len(data["category_number"]))
    datum = database.get_merch_item(data["category_number"], good_num)
    try:
        id, name, description, cost = datum
    except:
        await callback.message.answer(
            "Категория пуста.", reply_markup=builder.as_markup()
        )
        return
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer(
            "Категория пуста.", reply_markup=builder.as_markup()
        )
        return
    answer = f"""
Категория: {categories[data["category_number"]]}
Товар {good_num} из {category_size}

Название: {name}
Цена: {cost} Lucky
Описание: {description}
    """
    builder.row(InlineKeyboardButton(text="Купить", callback_data=f"BuyMerch_{id}"))
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data=f"ShowMerchChange_{good_num-1 if good_num != 1 else 0}",
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data=f"ShowMerchChange_{2 if category_size > good_num else 0}",
        ),
    )
    await state.set_data({"category_number": data["category_number"]})
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("BuyMerch_"))
async def buy_merch(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    merch_id = callback.data.split("_")[1]
    lucky = database.get_money_by_chat_id("lucky", callback.message.chat.id)
    data = database.get_merch_name_cost_by_merch_id(merch_id)
    name, needed_lucky = data
    if needed_lucky > lucky:
        await callback.message.answer(
            "Вы не можете купить %s, у вас %s Lucky, а требуется %s"
            % (name, lucky, needed_lucky),
            reply_markup=builder.as_markup(),
        )
        return
    builder.row(
        InlineKeyboardButton(
            text="Подтвердить", callback_data="BuyMerchConfirm_%s" % merch_id
        )
    )
    await callback.message.answer(
        "Вы точно хотите купить %s за %s Lucky? у вас %s Lucky"
        % (name, needed_lucky, lucky),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("BuyMerchConfirm_"))
async def buy_merch_confirm(callback: CallbackQuery, state: State):
    merch_id = callback.data.split("_")[1]
    data = database.get_lucky_id_level_xp_by_chat_id(callback.message.chat.id)
    lucky, user_id, level, xp = data
    data = database.get_merch_id_name_cost_by_merch_id(merch_id)
    name, needed_lucky = data
    if needed_lucky > lucky:
        await callback.message.answer(
            "Вы не можете купить %s, у вас %s Lucky, а требуется %s"
            % (name, lucky, needed_lucky)
        )
        return
    cur_limit = 50 + level * 25
    xp += needed_lucky * 3
    while xp > cur_limit:
        level += 1
        xp -= cur_limit
        cur_limit = 50 + level * 25
    database.set_xp_and_level_to_chat_id(xp, level, callback.message.chat.id)
    database.create_order(merch_id, needed_lucky, user_id)
    database.set_money_by_user_id("-", "lucky", needed_lucky, user_id)
    await callback.message.answer(
        f"Вы успешно заказали {name} за {needed_lucky} Lucky!\nС вами свяжутся. Советуем не удалять это сообщение."
    )
