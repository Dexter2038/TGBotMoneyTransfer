from aiogram import F, Router

router = Router()
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
from main import AdminStates
from config import currencies, course

import re


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
        InlineKeyboardButton(text="Войти в панель админа", callback_data="Admin")
    )
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
        InlineKeyboardButton(
            text="Написать личное сообщение", callback_data="WriteMessage"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Просмотреть пользователей", callback_data="ShowUsers"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Просмотреть транзакции", callback_data="ShowTransactionsAdmin"
        )
    )
    builder.add(
        InlineKeyboardButton(text="Просмотреть мерч", callback_data="ShowMerchAdmin")
    )
    builder.add(
        InlineKeyboardButton(
            text="Добавить предмет в мерч", callback_data="AddMerchItem"
        )
    )
    builder.add(
        InlineKeyboardButton(text="Просмотреть квизы", callback_data="EditQuizzesAdmin")
    )
    builder.add(
        InlineKeyboardButton(
            text="Добавить категорию в мерч", callback_data="AddMerchItemCategory"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Просмотреть не доставленный мерч", callback_data="NotDeliveredMerch_0"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Просмотреть доставленный мерч", callback_data="DeliveredMerch_0"
        )
    )
    builder.add(
        InlineKeyboardButton(text="Изменить курс", callback_data="ChangeCourse")
    )
    builder.add(
        InlineKeyboardButton(text="Сделать рассылку", callback_data="StartMailing")
    )
    builder.add(
        InlineKeyboardButton(text="Добавить администратора", callback_data="Addmin")
    )
    builder.add(
        InlineKeyboardButton(text="Снять администратора", callback_data="SubAdmin")
    )
    builder.adjust(2)
    await callback.message.answer(
        f"Добро пожаловать, Баркалов Михаил.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("NotDeliveredMerch_"))
async def see_not_delivered_merch(callback: CallbackQuery, state: FSMContext):
    page = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    orders = database.get_delivering_merch_by_status(0, page * 10)
    unanswered_orders = database.get_orders_len_by_status(0)
    answer = ""
    if not orders:
        await callback.message.answer(
            "Недоставленного мерча нет.", reply_markup=builder.as_markup()
        )
        return
    for idx, quiz in enumerate(orders, start=1):
        order_id, username, merch_name, cost = quiz
        answer += f"{idx}. Название товара: {merch_name}. Цена: {cost} Lucky. Покупатель: {username}.\n"
        builder.add(
            InlineKeyboardButton(text=f"{id}", callback_data=f"EditOrder_{order_id}")
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="DeliveredMerch_{}".format(page - 1 if page != 0 else 0),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="DeliveredMerch_{}".format(
                page + 1 if unanswered_orders < len(orders) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("DeliveredMerch_"))
async def see_delivered_merch(callback: CallbackQuery, state: FSMContext):
    page = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    orders = database.get_delivering_merch_by_status(1, page * 10)
    answered_orders = database.get_orders_len_by_status(1)
    answer = ""
    if not orders:
        await callback.message.answer(
            "Доставленного мерча нет.", reply_markup=builder.as_markup()
        )
        return
    for idx, quiz in enumerate(orders, start=1):
        order_id, username, merch_name, cost = quiz
        answer += f"{idx}. Название товара: {merch_name}. Цена: {cost} Lucky. Покупатель: {username}.\n"
        builder.add(
            InlineKeyboardButton(text=f"{id}", callback_data=f"EditOrder_{order_id}")
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="DeliveredMerch_{}".format(page - 1 if page != 0 else 0),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="DeliveredMerch_{}".format(
                page + 1 if answered_orders < len(orders) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("EditOrder_"))
async def edit_order_admin(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    data = database.get_merch_id_merch_name_merch_cost_order_cost_orderer_first_name_last_name_orderer_id_username_order_status_made_in_by_order_id(
        order_id
    )
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
            InlineKeyboardButton(
                text="Пометить недоставленным", callback_data="EditOrderUnmarked_"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Пометить доставленным", callback_data="EditOrderMarked_"
            )
        )
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
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    order_id = callback.data.split("_")[1]
    database.set_order_status(0, order_id)
    await callback.message.answer(
        "Статус успешно изменён на недоставленный.", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("EditOrderUnmarked"))
async def edit_order_unmarked(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    order_id = callback.data.split("_")[1]
    database.set_order_status(1, order_id)
    await callback.message.answer(
        "Статус успешно изменён на доставленный.", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "ChangeCourse")
async def change_course(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    answer = "Курсы валют:\n"
    for currency in currencies:
        answer += f"{currency}: {course[currency]}\n"
        builder.row(
            InlineKeyboardButton(
                text=f"Изменить курс {currency}",
                callback_data=f"ChangeCourse_{currency}",
            )
        )
    await callback.message.answer(
        f"{answer}Курс какой валюты вы хотите изменить?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("ChangeCourse_"))
async def change_value_course(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    currency = callback.data.split("_")[1]
    answer = "Курсы валют:\n"
    for currency in currencies:
        answer += f"{currency}: {course[currency]}\n"
    await callback.message.answer(
        text=f"{answer}Напишите число, на которое хотите изменить курс {currency}"
    )
    await state.set_state(AdminStates.change_course)
    await state.set_data({"currency": currency})


@router.message(AdminStates.change_course)
async def change_value_course_enter(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        await state.clear()
        return
    value = int(search.group())
    data = await state.get_data()
    builder.row(
        InlineKeyboardButton(
            text="Подтвердить",
            callback_data="ChangeCourseConfirm_{}_{}".format(data["currency"], value),
        )
    )
    await message.answer(
        text="Вы точно хотите сменить курс, поставив значение {} на {}?".format(
            data["currency"], value
        ),
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("ChangeCourseConfirm_"))
async def change_value_course_confirm(callback: CallbackQuery, state: FSMContext):
    _, currency, value = callback.data.split("_")
    with open("course.txt", encoding="utf-8", mode="r") as f:
        curs = list(map(lambda x: int(x.replace("\n", "")), f.readlines()))
    curs[currencies.index(currency)] = value
    with open("course.txt", "w") as f:
        f.write("")
    with open("course.txt", "a") as f:
        for cur in curs:
            f.write(str(cur) + "\n")
    course[currency] = value
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        f"Вы успешно изменили курс {currency} на {value}",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("SeeTransactionsQR_"))
async def see_qr_transactions(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    _, page, user_id = callback.data.split("_")
    page = int(page)
    user_id = int(user_id)
    builder = InlineKeyboardBuilder()
    trns_num = database.get_transactions_len_by_user(user_id)
    results = database.get_transactions_page(page, user_id)
    if not results:
        await callback.message.answer("Пусто. Транзакции отсутствуют.")
        return
    out_results = "Транзакции {}-{} из {}\n\n".format(
        1 + 10 * page, len(results) + 10 * page, trns_num
    )
    for idx, trans in enumerate(results):
        idx += 1
        (
            id,
            trans_type,
            first_amount,
            first_currency,
            second_amount,
            second_currency,
            from_user,
            to_user,
            what_bought,
            made_in,
        ) = trans
        builder.add(
            InlineKeyboardButton(text=str(idx), callback_data="Transaction_" + str(id))
        )
        last_name, first_name = database.get_name_by_user_id(user_id)
        match trans_type:
            case 0:
                out_results += "{}. {} {}. Обмен валют.  Из {} {} в {} {}. {}\n".format(
                    idx,
                    last_name,
                    first_name,
                    first_amount,
                    currencies[first_currency],
                    second_amount,
                    currencies[second_currency],
                    made_in,
                )
            case 1:
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    user_id
                )
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        last_name,
                        first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    )
                )
            case 2:
                out_results += "{}. {} {}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, last_name, first_name, first_amount, made_in
                )
            case 3:
                out_results += "{}. {} {}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, last_name, first_name, what_bought, first_amount, made_in
                )
            case 4:
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    user_id
                )
                out_results += "{}. Начисление от администратора {} {} клиенту {} {} {} {}. {}\n".format(
                    idx,
                    last_name,
                    first_name,
                    to_user_last_name,
                    to_user_first_name,
                    first_amount,
                    currencies[first_currency],
                    made_in,
                )
            case 5:
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    user_id
                )
                out_results += "{}. Снятие от администратора {} {} у клиента {} {} {} {}. {}\n".format(
                    idx,
                    last_name,
                    first_name,
                    to_user_last_name,
                    to_user_first_name,
                    first_amount,
                    currencies[first_currency],
                    made_in,
                )
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="SeeTransactionsQR_{}_{}".format(
                page - 1 if page != 0 else 0, user_id
            ),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="SeeTransactionsQR_{}_{}".format(
                page + 1 if trns_num < len(results) + 10 * page else page, user_id
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())
