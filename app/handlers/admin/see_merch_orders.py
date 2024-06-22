from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from app.utils import database

router = Router(name="admin-merch-orders-watch")


@router.callback_query(F.data.startswith("NotDeliveredMerch_"))
async def see_not_delivered_merch(callback: CallbackQuery, state: FSMContext):
    page = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    orders = database.get_delivering_merch_by_status(0, page * 10)
    unanswered_orders = database.get_orders_len_by_status(0)
    answer = ""
    if not orders:
        await callback.message.answer("Недоставленного мерча нет.",
                                      reply_markup=builder.as_markup())
        return
    for idx, quiz in enumerate(orders, start=1):
        order_id, username, merch_name, cost = quiz
        answer += f"{idx}. Название товара: {merch_name}. Цена: {cost} Lucky. Покупатель: {username}.\n"
        builder.add(
            InlineKeyboardButton(text=f"{id}",
                                 callback_data=f"EditOrder_{order_id}"))
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="DeliveredMerch_{}".format(page -
                                                     1 if page != 0 else 0),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="DeliveredMerch_{}".format(
                page + 1 if unanswered_orders < len(orders) +
                10 * page else page),
        ),
    )
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("DeliveredMerch_"))
async def see_delivered_merch(callback: CallbackQuery, state: FSMContext):
    page = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    orders = database.get_delivering_merch_by_status(1, page * 10)
    answered_orders = database.get_orders_len_by_status(1)
    answer = ""
    if not orders:
        await callback.message.answer("Доставленного мерча нет.",
                                      reply_markup=builder.as_markup())
        return
    for idx, quiz in enumerate(orders, start=1):
        order_id, username, merch_name, cost = quiz
        answer += f"{idx}. Название товара: {merch_name}. Цена: {cost} Lucky. Покупатель: {username}.\n"
        builder.add(
            InlineKeyboardButton(text=f"{id}",
                                 callback_data=f"EditOrder_{order_id}"))
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="DeliveredMerch_{}".format(page -
                                                     1 if page != 0 else 0),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="DeliveredMerch_{}".format(
                page + 1 if answered_orders < len(orders) +
                10 * page else page),
        ),
    )
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("EditOrder_"))
async def edit_order_admin(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    data = database.get_merch_id_merch_name_merch_cost_order_cost_orderer_first_name_last_name_orderer_id_username_order_status_made_in_by_order_id(
        order_id)
    (
        merch_id,
        name,
        cost,
        order_cost,
        first_name,
        last_name,
        user_id,
        username,
        status,
        made_in,
    ) = data
    if status:
        builder.row(
            InlineKeyboardButton(text="Пометить недоставленным",
                                 callback_data="EditOrderUnmarked_"))
    else:
        builder.row(
            InlineKeyboardButton(text="Пометить доставленным",
                                 callback_data="EditOrderMarked_"))
    await callback.message.answer(
        f"""
ID заказа: {order_id}
ID пользователя заказчика: {user_id}
Заказчик: {last_name} {first_name}
Никнейм заказчика в тг: {username}
ID товара: {merch_id}
Название товара: {name}
Цена товара: {cost}
Сумма покупки: {order_cost}
Статус покупки: {"Оплачен, но не доставлен" if status == 0 else "Оплачен и доставлен"}
Заказ сделан в: {made_in}""",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("EditOrderUnmarked"))
async def edit_order_unmarked(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    order_id = callback.data.split("_")[1]
    database.set_order_status(0, order_id)
    await callback.message.answer("Статус успешно изменён на недоставленный.",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("EditOrderUnmarked"))
async def edit_order_unmarked(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    order_id = callback.data.split("_")[1]
    database.set_order_status(1, order_id)
    await callback.message.answer("Статус успешно изменён на доставленный.",
                                  reply_markup=builder.as_markup())
