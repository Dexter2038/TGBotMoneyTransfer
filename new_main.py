import asyncio
import datetime
import io
import logging
from os import getenv, environ

from aiogram import Bot, types, F, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.token import TokenValidationError
import sqlite3
import segno
import re
import cv2
import json
import config
import os

config.Initializer()
transactions_per_page = 10
users_per_page = 10

currencies = {0: "Lucky", 1: "Cash Online", 2: "Another Value"}
currencies_reverse = {"Lucky": 0, "Cash Online": 1, "Another Value": 2}
transactions = [
    "Обмен валют",
    "Перевод",
    "Вывод монет",
    "Покупка",
    "Начисление от администратора",
    "Снятие от администратора",
]
categories = ["Футболки", "Кепки"]
admin_rights = {0: "Главный разработчик"}


if os.path.isfile("categories.txt"):
    with open("categories.txt", encoding="utf-8", mode="r") as categories_file:
        categories = list(
            map(lambda x: x.replace("\n", ""), categories_file.readlines())
        )

course = {"Lucky": 2, "Cash Online": 1, "Another Value": 3}


def convert_value(amount: int, current_currency: str, next_currency: str) -> int:
    return int(amount * course[next_currency] / course[current_currency])


con = sqlite3.connect("database.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    first_name CHAR(50) NOT NULL,
    last_name CHAR(50) NOT NULL,
    level INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0,
    username CHAR(50) NOT NULL,
    cash_online INTEGER NOT NULL DEFAULT 0,
    lucky INTEGER NOT NULL DEFAULT 0,
    another_value INTEGER NOT NULL DEFAULT 0,
    admin INTEGER NOT NULL DEFAULT 0,
    registered_at DATETIME NOT NULL DEFAULT (datetime('now','localtime')))"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS admins(
    admin_id INTEGER PRIMARY KEY,
    login CHAR(50) NOT NULL,
    password CHAR(255) NOT NULL,
    powers INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE)"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY,
    trans_type INTEGER NOT NULL,
    first_amount INTEGER NOT NULL,
    second_amount INTEGER,
    from_user INTEGER,
    to_user INTEGER,
    first_currency INTEGER NOT NULL,
    second_currency INTEGER DEFAULT NULL,
    what_bought TEXT DEFAULT NULL,
    made_in DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (from_user) REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE SET NULL,
    FOREIGN KEY (to_user) REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE SET NULL)"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS withdraw_qrs(
    id INTEGER PRIMARY KEY,
    status INTEGER NOT NULL DEFAULT 0,
    amount INTEGER NOT NULL
    )"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS merch(
    id INTEGER PRIMARY KEY,
    name CHAR(255) NOT NULL,
    category INTEGER NOT NULL,
    description TEXT NOT NULL,
    cost INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now','localtime')))"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS quizzes(
    id INTEGER PRIMARY KEY,
    name CHAR(255) NOT NULL,
    description TEXT NOT NULL,
    reward TEXT NOT NULL
    )"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS questions(
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER,
    question TEXT NOT NULL,
    first_answer CHAR(50) NOT NULL,
    second_answer CHAR(50) NOT NULL,
    third_answer CHAR(50) NOT NULL,
    fourth_answer CHAR(50) NOT NULL,
    correct_answer INTEGER NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE ON UPDATE CASCADE)"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY,
    merch_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    cost INTEGER NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    made_in DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
    )"""
)
try:
    bot = Bot(token=getenv("tgBotToken"))
    bot_type = getenv("botType")

except TokenValidationError:
    logging.error("Invalid telegram bot token")
    exit(1)
except:
    logging.error("Invalid")
    exit(1)

dp = Dispatcher(bot=bot)
cur.execute(
    """
    INSERT INTO withdraw_qrs (amount) VALUES (0)"""
)
cur.execute("UPDATE users SET admin = 1 WHERE user_id = 1")
cur.execute(
    'INSERT INTO admins (login, password, powers, user_id) VALUES ("Login", "PASS", 0, 1)'
)
cur.execute("INSERT INTO orders (user_id, merch_id, cost) VALUES (1, 1, 400)")


class UserStates(StatesGroup):
    start = State()
    register = State()
    profile = State()
    about_us = State()
    merch = State()
    login = State()
    password = State()
    exchange_value_to_value = State()
    give_money = State()
    give_money_to_person = State()
    withdraw_money = State()
    add_money = State()
    substract_money = State()
    change_user_value = State()
    create_merch_photo = State()
    create_merch_name = State()
    create_merch_description = State()
    create_merch_cost = State()
    merch_change_property = State()
    add_quiz = State()
    add_merch_category = State()
    add_question_quiz = State()
    edit_question_question = State()
    edit_answer_question = State()
    edit_correct_answer_question = State()


@dp.message(UserStates.register)
async def register_user(message: Message, state: FSMContext):
    if len(message.text.split(" ")) != 2:
        await message.answer("Введите пожалуйста ваше имя и фамилию через пробел")
        await state.set_state(UserStates.register)
        return
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В профиль", callback_data="Profile"))
    first_name, last_name = message.text.split(" ")
    cur.execute(
        f"""
        INSERT INTO users (chat_id, first_name, last_name, level, username, cash_online, lucky, another_value, registered_at) VALUES
        ({message.chat.id}, "{first_name}", "{last_name}", 0, "{message.from_user.username}", 111111, 111111, 111111, CURRENT_TIMESTAMP)
    """
    )
    con.commit()
    await message.answer(
        f"Вы успешно зарегистрированы, {last_name} {first_name}.",
        reply_markup=builder.as_markup(),
    )
    await state.clear()


@dp.callback_query(F.data == "Profile")
async def profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    cur.execute(
        f"""
        SELECT first_name, level, cash_online, lucky, another_value FROM users WHERE chat_id = {callback.message.chat.id}
    """
    )
    first_name, level, cash_online, lucky, another_value = cur.fetchone()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="История транзакций", callback_data="Transactions")
    )
    builder.add(
        InlineKeyboardButton(text="Обменять монеты", callback_data="ExchangeMoney")
    )
    builder.add(InlineKeyboardButton(text="Передать монеты", callback_data="GiveMoney"))
    builder.add(
        InlineKeyboardButton(text="Вывести Cash Online", callback_data="WithdrawMoney")
    )
    builder.adjust(2)
    await callback.message.answer(
        f"""Здравствуйте, {first_name}.
Ваш уровень: {level}
Баланс:
Lucky: {lucky}
CashOnline: {cash_online}
Другая валюта: {another_value}""",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "Transactions")
async def transactions(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Просмотреть историю транзакций", callback_data="ShowTransactions"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Показать историю транзакцию (QRCode)",
            callback_data="ShowQRTransactions",
        )
    )
    builder.adjust(1)
    await callback.message.answer(
        text="Просмотреть историю транзакций здесь или получить QR-код, чтобы показать историю транзакций?",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ShowTransactions")
async def see_transactions(callback: CallbackQuery, state: FSMContext):
    cur.execute(f"SELECT user_id FROM users WHERE chat_id = {callback.message.chat.id}")
    user_id = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM transactions WHERE from_user = {} OR to_user = {}".format(
            user_id, user_id
        )
    )
    trans_num = cur.fetchone()[0]
    await state.set_data({"user_id": user_id, "trns_num": trans_num})
    builder = InlineKeyboardBuilder()
    cur.execute(
        f"""
        SELECT id, trans_type, first_amount, first_currency, second_amount, second_currency, from_user, to_user, what_bought, made_in FROM transactions
WHERE from_user = {user_id} OR to_user = {user_id} LIMIT {transactions_per_page} OFFSET 0"""
    )
    results = cur.fetchall()
    if not results:
        await bot.answer_callback_query(callback.id, "Транзакции отсутствуют")
        builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
        await callback.message.answer(
            text="Транзакции отсутствуют", reply_markup=builder.as_markup()
        )
        return
    out_results = "Транзакции 1-{} из {}\n\n".format(len(results), trans_num)
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
        match trans_type:
            case 0:
                out_results += "{}. Обмен валют. Из {} {} в {} {}. {}\n".format(
                    idx,
                    first_amount,
                    currencies[first_currency],
                    second_amount,
                    currencies[second_currency],
                    made_in,
                )
            case 1:
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % from_user
                )
                from_user_last_name, from_user_first_name = cur.fetchone()
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        from_user_last_name,
                        from_user_first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    )
                )
            case 2:
                out_results += "{}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, first_amount, made_in
                )
            case 3:
                out_results += "{}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, what_bought, first_amount, made_in
                )
            case 4:
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % from_user
                )
                from_user_last_name, from_user_first_name = cur.fetchone()
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
                out_results += "{}. Начисление от администратора {} {} клиенту {} {} {} {}. {}\n".format(
                    idx,
                    from_user_last_name,
                    from_user_first_name,
                    to_user_last_name,
                    to_user_first_name,
                    first_amount,
                    currencies[first_currency],
                    made_in,
                )
            case 5:
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % from_user
                )
                from_user_last_name, from_user_first_name = cur.fetchone()
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
                out_results += "{}. Снятие от администратора {} {} у клиента {} {} {} {}. {}\n".format(
                    idx,
                    from_user_last_name,
                    from_user_first_name,
                    to_user_last_name,
                    to_user_first_name,
                    first_amount,
                    currencies[first_currency],
                    made_in,
                )
    builder.row(
        InlineKeyboardButton(text="⬅", callback_data="TransactionPageChange_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                1 if trans_num < len(results) else 0
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("TransactionPageChange_"))
async def see_transaction_change_page(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    page = int(callback.data.split("_")[1])
    await state.set_data(data)
    builder = InlineKeyboardBuilder()
    cur.execute(
        f"""
        SELECT id, trans_type, first_amount, first_currency, second_amount, second_currency, from_user, to_user, what_bought, made_in FROM transactions
WHERE from_user = {data["user_id"]} OR to_user = {data["user_id"]} LIMIT {transactions_per_page} OFFSET {transactions_per_page*page}"""
    )
    results = cur.fetchall()
    if not results:
        await bot.answer_callback_query(callback.id, "Пусто")
        return
    out_results = "Транзакции {}-{} из {}\n\n".format(
        1 + 10 * page, len(results) + 10 * page, data["trns_num"]
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
        match trans_type:
            case 0:
                out_results += "{}. Обмен валют. Из {} {} в {} {}. {}\n".format(
                    idx,
                    first_amount,
                    currencies[first_currency],
                    second_amount,
                    currencies[second_currency],
                    made_in,
                )
            case 1:
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % from_user
                )
                from_user_last_name, from_user_first_name = cur.fetchone()
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        from_user_last_name,
                        from_user_first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    )
                )
            case 2:
                out_results += "{}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, first_amount, made_in
                )
            case 3:
                out_results += "{}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, what_bought, first_amount, made_in
                )
            case 4:
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % from_user
                )
                from_user_last_name, from_user_first_name = cur.fetchone()
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
                out_results += "{}. Начисление от администратора {} {} клиенту {} {} {} {}. {}\n".format(
                    idx,
                    from_user_last_name,
                    from_user_first_name,
                    to_user_last_name,
                    to_user_first_name,
                    first_amount,
                    currencies[first_currency],
                    made_in,
                )
            case 5:
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % from_user
                )
                from_user_last_name, from_user_first_name = cur.fetchone()
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
                out_results += "{}. Снятие от администратора {} {} у клиента {} {} {} {}. {}\n".format(
                    idx,
                    from_user_last_name,
                    from_user_first_name,
                    to_user_last_name,
                    to_user_first_name,
                    first_amount,
                    currencies[first_currency],
                    made_in,
                )
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="TransactionPageChange_{}".format(
                page - 1 if page != 0 else 0
            ),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                page + 1 if data["trns_num"] < len(results) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("Transaction_"))
async def see_transaction_detailed(callback: CallbackQuery, state: FSMContext):
    id = callback.data.split("_")[1]
    cur.execute(
        f"SELECT trans_type, first_amount, first_currency, second_amount, second_currency, from_user, to_user, what_bought, made_in FROM transactions WHERE id = {id}"
    )
    (
        trans_type,
        first_amount,
        first_currency,
        second_amount,
        second_currency,
        from_user,
        to_user,
        what_bought,
        made_in,
    ) = cur.fetchone()
    match trans_type:
        case 0:
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
            )
            from_user_last_name, from_user_first_name = cur.fetchone()
            answer = """
ID транзакции: {}.
Тип: Обмен валют.
Клиент: {} {}.
Начальная сумма: {}.
Начальная валюта: {}.
Конечная сумма: {}.
Конечная валюта: {}.
Дата и время: {}.
            """.format(
                id,
                from_user_last_name,
                from_user_first_name,
                first_amount,
                currencies[first_currency],
                second_amount,
                currencies[second_currency],
                made_in,
            )
        case 1:
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
            )
            from_user_last_name, from_user_first_name = cur.fetchone()
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % to_user
            )
            to_user_last_name, to_user_first_name = cur.fetchone()
            answer = """
ID транзакции: {}.
Тип: Перевод от клиента клиенту.
Сумма: {}.
Валюта: {}.
Отправитель: {} {}.
Получатель: {} {}.
Дата и время: {}.
            """.format(
                id,
                first_amount,
                currencies[first_currency],
                from_user_last_name,
                from_user_first_name,
                to_user_last_name,
                to_user_first_name,
                made_in,
            )
        case 2:
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
            )
            from_user_last_name, from_user_first_name = cur.fetchone()
            answer = """
ID транзакции: {}.
Тип: Вывод монет.
Сумма: {}.
Валюта: Cash Online.
Клиент: {} {}.
Дата и время: {}.
            """.format(
                id,
                first_amount,
                from_user_last_name,
                from_user_first_name,
                made_in,
            )
        case 3:
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
            )
            from_user_last_name, from_user_first_name = cur.fetchone()
            answer = """
ID транзакции: {}.
Тип: Покупка мерча.
Сумма: {}.
Валюта: Lucky.
Клиент: {} {}.
Товар: {}.
Дата и время: {}.
            """.format(
                id,
                first_amount,
                from_user_last_name,
                from_user_first_name,
                what_bought,
                made_in,
            )
        case 4:
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
            )
            from_user_last_name, from_user_first_name = cur.fetchone()
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % to_user
            )
            to_user_last_name, to_user_first_name = cur.fetchone()
            answer = """
ID транзакции: {}.
Тип: Перевод клиенту от администратора.
Сумма: {}.
Валюта: {}.
Администратор: {} {}.
Клиент: {} {}.
Дата и время: {}.
            """.format(
                id,
                first_amount,
                currencies[first_currency],
                from_user_last_name,
                from_user_first_name,
                to_user_last_name,
                to_user_first_name,
                made_in,
            )
        case 5:
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
            )
            from_user_last_name, from_user_first_name = cur.fetchone()
            cur.execute(
                "SELECT last_name, first_name FROM users WHERE user_id = %s" % to_user
            )
            to_user_last_name, to_user_first_name = cur.fetchone()
            answer = """
ID транзакции: {}.
Тип: Снятие монет у клиента администратором.
Сумма: {}.
Валюта: {}.
Администратор: {} {}.
Клиент: {} {}.
Дата и время: {}.
            """.format(
                id,
                first_amount,
                currencies[first_currency],
                from_user_last_name,
                from_user_first_name,
                to_user_last_name,
                to_user_first_name,
                made_in,
            )
    await callback.message.answer(answer)


@dp.callback_query(F.data == "ShowQRTransactions")
async def show_transactions(callback: CallbackQuery, state: FSMContext):
    qr = segno.make_qr("Transaction completed in 12:20")
    qr.save("QR.png", scale=10)
    qr = FSInputFile("QR.png")
    await callback.message.answer_photo(qr, "QR код для пользователя тэтатэ")


@dp.callback_query(F.data == "ExchangeMoney")
async def exchange_money(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Lucky на Cash Online",
            callback_data="Exchange-LuckyToCash_Online",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Cash Online на Lucky",
            callback_data="Exchange-Cash_OnlineToLucky",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Lucky на Another Value",
            callback_data="Exchange-LuckyToAnother_Value",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Another Value на Lucky",
            callback_data="Exchange-Another_ValueToLucky",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Cash Online на Another Value",
            callback_data="Exchange-Cash_OnlineToAnother_Value",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Обменять Another Value на Cash Online",
            callback_data="Exchange-Another_ValueToCash_Online",
        )
    )
    await callback.message.answer(
        "Какую валюту на какую вы хотиsте обменять?", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("Exchange-"))
async def exchange_value_to_value(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="ExchangeMoney"))
    currencyes = callback.data.split("-")[1].split("To")
    print(currencyes[0].lower(), currencyes[1].lower())
    cur.execute(
        f"""
    SELECT {currencyes[0].lower()}, {currencyes[1].lower()} FROM users WHERE chat_id = {callback.message.chat.id}
    """
    )
    availables = cur.fetchone()
    first_available, second_available = availables
    first, second = map(lambda x: x.replace("_", " "), currencyes)
    response = f"""
У вас {first_available} {first} и {second_available} {second}.
Курс: {course[first]} {first} = {course[second]} {second}."""
    if course[first] > course[second]:
        response += """
Напишите, сколько монет вы хотите получить.
"""
        await state.set_data(
            {
                "transfer": "to",
                "first": first,
                "second": second,
                "first_available": first_available,
                "first_currency": currencyes[0].lower(),
                "second_currency": currencyes[1].lower(),
            }
        )
    else:
        response += f"""
Напишите, сколько монет вы хотите обменять на {second}.
"""
        await state.set_data(
            {
                "transfer": "from",
                "first": first,
                "second": second,
                "first_available": first_available,
                "first_currency": currencyes[0].lower(),
                "second_currency": currencyes[1].lower(),
            }
        )
    await state.set_state(UserStates.exchange_value_to_value)
    await callback.message.answer(text=response, reply_markup=builder.as_markup())


@dp.message(UserStates.exchange_value_to_value)
async def enter_exchange_value_to_value(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="ExchangeMoney"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    result = int(search.group())
    data = await state.get_data()
    await state.clear()
    needed = (
        convert_value(result, data["second"], data["first"])
        if data["transfer"] == "to"
        else result
    )
    if data["first_available"] < needed:
        await message.answer(
            f"""
У вас недостаточно монет.
У вас {data["first_available"]} {data["first"]}.
""",
            reply_markup=builder.as_markup(),
        )
        return
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmExchangeValue")
    )
    out = convert_value(needed, data["first"], data["second"])
    await state.set_data(
        {
            "available": data["first_available"],
            "needed": needed,
            "out": out,
            "needed_currency": data["first"],
            "out_currency": data["second"],
        }
    )
    await message.answer(
        text=f"""Вы хотите обменять {needed} {data["first"]} на {out} {data["second"]}?""",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmExchangeValue")
async def confirm_exchange_value_to_value(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Вернуться", callback_data="ExchangeMoney"))
    data = await state.get_data()
    cur.execute(
        f"""
        SELECT {data["needed_currency"].lower().replace(" ","_")}, user_id FROM users WHERE chat_id = {callback.message.chat.id}
    """
    )
    available, user_id = cur.fetchone()
    if available < data["needed"]:
        await callback.message.answer(
            f"""
У вас недостаточно монет.
У вас {available} {data["needed_currency"]}""",
            reply_markup=builder.as_markup(),
        )
        await bot.answer_callback_query(callback.id, text="Недостаточно монет.")
        return
    cur.execute(  # минус требуемые монеты
        f"""
        UPDATE users SET {data["needed_currency"].lower().replace(" ","_")} = {data["needed_currency"].lower().replace(" ","_")} - {data["needed"]} WHERE chat_id = {callback.message.chat.id}
    """
    )
    cur.execute(  # плюс нужные монеты
        f"""
        UPDATE users SET {data["out_currency"].lower().replace(" ","_")} = {data["out_currency"].lower().replace(" ","_")} + {data["out"]} WHERE chat_id = {callback.message.chat.id}
"""
    )
    cur.execute(
        """
    INSERT INTO transactions (trans_type, from_user, first_amount, first_currency, second_amount, second_currency)
    VALUES (0, %s, %s, %s, %s, %s)
    """
        % (
            user_id,
            data["needed"],
            currencies_reverse[data["needed_currency"]],
            data["out"],
            currencies_reverse[data["out_currency"]],
        )
    )
    con.commit()
    await callback.message.answer(
        f"""Вы обменяли {data["needed"]} {data["needed_currency"]} на {data["out"]} {data["out_currency"]}."""
    )
    await bot.answer_callback_query(callback.id, "Обмен валют прошел успешно.")


@dp.callback_query(F.data == "GiveMoney")
async def give(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    builder.row(InlineKeyboardButton(text="Lucky", callback_data="Give-Lucky"))
    builder.row(
        InlineKeyboardButton(text="Cash Online", callback_data="Give-Cash_Online")
    )
    builder.row(
        InlineKeyboardButton(text="Another Value", callback_data="Give-Another_Value")
    )
    await callback.message.answer(
        "Какую валюту Вы хотите передать?", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("Give-"))
async def give_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("-")[1]
    cur.execute(
        f"""
SELECT {currency.lower()} FROM users WHERE chat_id = {callback.message.chat.id}
"""
    )
    available = cur.fetchone()[0]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    await callback.message.answer(
        f"""
У Вас {available} {currency.replace("_"," ")}.
Сколько монет Вы хотите передать?""",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(UserStates.give_money)
    await state.set_data({"available": available, "currency": currency})


@dp.message(UserStates.give_money)
async def give_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    result = int(search.group())
    if result > data["available"]:
        await message.answer(
            text=f"""
Недостаточно монет.
У вас {data["available"]} {data["currency"].replace("_", " ")}.
""",
            reply_markup=builder.as_markup(),
        )
        return
    await state.set_data({"amount": result, **data})
    await state.set_state(UserStates.give_money_to_person)
    await message.answer(
        text=f"""
Кому вы хотите перевести {result} {data["currency"].replace("_"," ")}?
Введите @username (указан в профиле)""",
        reply_markup=builder.as_markup(),
    )


@dp.message(UserStates.give_money_to_person)
async def give_money_to_person(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    username = message.text.split(" ")[0]
    if username[0] == "@":
        username = username[1:]
    cur.execute(
        f"""
SELECT first_name, last_name, user_id FROM users WHERE username = "{username}"
"""
    )
    cur_data = cur.fetchone()
    if not cur_data:
        await message.answer(
            """
Такой пользователь не найден.
Введите имя пользователя.""",
            reply_markup=builder.as_markup(),
        )
        return
    first_name, last_name, to_user_id = cur_data
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmGiveMoney")
    )
    await message.answer(
        f"""
Вы хотите передать {data["amount"]} {data["currency"].replace("_"," ")} пользователю {last_name} {first_name}?
    """,
        reply_markup=builder.as_markup(),
    )
    await state.set_data(
        {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "to_user_id": to_user_id,
            **data,
        }
    )


@dp.callback_query(F.data == "ConfirmGiveMoney")
async def give_money_to_person_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    cur.execute(
        f"""
        SELECT {data["currency"].lower()}, user_id FROM users WHERE chat_id = {callback.message.chat.id}
    """
    )
    available, from_user_id = cur.fetchone()
    if available < data["amount"]:
        await callback.message.answer(
            """
У Вас недостаточно монет.
У Вас {available} {data["currency]}.""",
            reply_markup=builder.as_markup(),
        )
        await bot.answer_callback_query(callback.id, text="Недостаточно монет.")
        return
    cur.execute(  # минус требуемые монеты
        f"""
        UPDATE users SET {data["currency"].lower()} = {data["currency"].lower()} - {data["amount"]} WHERE chat_id = {callback.message.chat.id}
    """
    )
    cur.execute(  # плюс нужные монеты
        f"""
        UPDATE users SET {data["currency"].lower()} = {data["currency"].lower()} + {data["amount"]} WHERE username = "{data["username"]}"
    """
    )
    cur.execute(
        """
    INSERT INTO transactions (trans_type, first_amount, from_user, to_user, first_currency) VALUES (1, %s, %s, %s, %s)"""
        % (
            data["amount"],
            from_user_id,
            data["to_user_id"],
            currencies_reverse[data["currency"].replace("_", " ")],
        )
    )
    con.commit()
    await callback.message.answer(
        f"""Вы передали {data["amount"]} {data["currency"]} пользователю {data["last_name"]} {data["first_name"]}."""
    )
    await state.clear()
    await bot.answer_callback_query(callback.id, "Перевод прошел успешно.")


@dp.callback_query(F.data == "WithdrawMoney")
async def withdraw_money(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    cur.execute(
        f"""
        SELECT cash_online FROM users WHERE chat_id = {callback.message.chat.id}
    """
    )
    available = cur.fetchone()[0]
    await callback.message.answer(
        f"""
У Вас {available} Cash Online монет.
Введите, сколько монет вы хотити вывести.
    """,
        reply_markup=builder.as_markup(),
    )
    await state.set_state(UserStates.withdraw_money)
    await state.set_data({"available": available})


@dp.message(UserStates.withdraw_money)
async def enter_withdraw_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
    data = await state.get_data()
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    result = int(search.group())
    if result > data["available"]:
        await message.answer(
            text=f"""
Недостаточно монет.
У вас {data["available"]} Cash Online.
""",
            reply_markup=builder.as_markup(),
        )
        return
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmWithdrawMoney")
    )
    await state.set_data({"amount": result})
    await message.answer(
        f"""
Вы хотите вывести {result} Cash Online?
    """,
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmWithdrawMoney")
async def confirm_withdraw_money(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cur.execute(f"SELECT user_id FROM users WHERE chat_id = {callback.message.chat.id}")
    user_id = cur.fetchone()[0]
    cur.execute(
        """
    SELECT id FROM withdraw_qrs ORDER BY id DESC LIMIT 1"""
    )
    id = cur.fetchone()[0] + 1
    cur.execute(
        """
    INSERT INTO withdraw_qrs (amount) VALUES (%s)"""
        % (data["amount"])
    )
    con.commit()
    message = '{"type" : "withdraw","qr_id" : %s,"amount" : %s,"user_id" : %s}' % (
        id,
        data["amount"],
        user_id,
    )
    qr = segno.make_qr(message)
    qr.save("QR.png", scale=15)
    qr = FSInputFile("QR.png")
    await callback.message.answer_photo(
        qr,
        """
Предъявите QRCode нашему сотруднику.
Он его отсканирует.""",
    )


@dp.callback_query(F.data == "Gifts")
async def gifts(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В профиль", callback_data="Profile"))
    builder.add(InlineKeyboardButton(text="Квизы", callback_data="Quizzes"))
    await callback.message.answer("Выберите опцию:", reply_markup=builder.as_markup())


@dp.callback_query(F.data == "Quizzes")
async def show_quizzes(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В профиль", callback_data="Profile"))
    cur.execute("SELECT name, id FROM quizzes")
    quizzes = cur.fetchall()
    for name in quizzes:
        name, id = name
        builder.add(InlineKeyboardButton(text=name, callback_data="Quiz_%s" % id))
    await callback.message.answer("Выберите квиз: ")


@dp.callback_query(F.data.startswith("Quiz_"))
async def show_quiz(callback: CallbackQuery, state: FSMContext):
    id = callback.data.split("_")[1]
    cur.execute(
        "SELECT name, description, reward FROM quizzes WHERE id = {}".format(id)
    )
    name, description, reward = cur.fetchone()
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    builder.add(
        InlineKeyboardButton(
            text="Далее", callback_data="Question_0_Quiz_{}".format(id)
        )
    )
    builder.adjust(2)
    await callback.message.answer(
        f"""
Тест {name}
{description}""",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data.startswith("Question_"))
async def show_question(callback: CallbackQuery, state: FSMContext):
    _, question_num, _, quiz_id = callback.data.split("_")
    cur.execute(
        f"SELECT question, first_answer, second_answer, third_answer, fourth_answer, correct_answer FROM questions WHERE quiz_id = {quiz_id} LIMIT 1 OFFSET {question_num}"
    )
    state_data = await state.get_data()
    rightanswers = state_data["right-answers"]
    data = cur.fetchone()
    if not data:
        cur.execute("SELECT COUNT(*) FROM questions WHERE quiz_id = {qioz_id}")
        correct_answers = cur.fetchone()[0]
        if correct_answers == rightanswers:
            pass  # Начислить награду
        else:
            await callback.message.answer(
                f"К сожалению, вы не выиграли приз, нужно ответить на все вопросы верно.\nВы ответили правильно на {rightanswers} из {correct_answers} вопросов"
            )
    (
        question,
        *answers,
        correct_answer,
    ) = data
    builder = InlineKeyboardBuilder()
    for id, answer in enumerate(answers):
        builder.add(
            InlineKeyboardButton(
                text=answer,
                callback_data=f"Answer_{id+1}_{correct_answer}_Question_{question_num}_Quiz_{quiz_id}_{rightanswers}",
            )
        )
    await callback.message.answer(question)


@dp.callback_query(F.data.startswith("Answer_"))
async def check_question(callback: CallbackQuery, state: FSMContext):
    _, answer, correct_answer, _, question_num, _, quiz_id, right_answers = (
        callback.data.split("_")
    )
    if answer == correct_answer:
        await state.set_data({"right-answers": right_answers + 1})
    else:
        await state.set_data({"right-answers": right_answers})
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Дальше", callback_data=f"Question_{question_num}_Quiz_{quiz_id}"
        )
    )
    await callback.message.answer("Дальше", reply_markup=builder.as_markup())


@dp.callback_query(F.data == "ShowMerch")
async def merch(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В профиль", callback_data="Profile"))
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


@dp.callback_query(F.data.startswith("ShowMerchCategory_"))
async def merch_category(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        *(
            InlineKeyboardButton(text="В профиль", callback_data="Profile"),
            InlineKeyboardButton(
                text="Выбрать другую категорию", callback_data="ShowMerch"
            ),
        )
    )
    category_number = int(callback.data.split("_")[1])
    cur.execute(f"SELECT COUNT(*) FROM merch WHERE category = {category_number}")
    category_size = int(cur.fetchone()[0])
    cur.execute(
        f"SELECT id, name, description, cost FROM merch WHERE category = {category_number} LIMIT 1 OFFSET 0"
    )
    try:
        id, name, description, cost = cur.fetchone()
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
        InlineKeyboardButton(text="⬅", callback_data="ShowMerchChange_1"),
        InlineKeyboardButton(
            text="➡",
            callback_data="ShowMerchChange_{}".format(2 if category_size > 1 else 1),
        ),
    )
    await state.set_data({"category_number": category_number})
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("ShowMerchChange_"))
async def merch_category_change(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        (
            InlineKeyboardButton(text="В профиль", callback_data="Profile"),
            InlineKeyboardButton(
                text="Выбрать другую категорию", callback_data="ShowMerch"
            ),
        )
    )
    data = await state.get_data()
    good_num = int(callback.data.split("_")[1])
    cur.execute(
        "SELECT COUNT(*) FROM merch WHERE category = %s" % data["category_number"]
    )
    category_size = int(cur.fetchone()[0])
    cur.execute(
        "SELECT id, name, description, cost FROM merch WHERE category = %s LIMIT 1 OFFSET %s"
        % data["category_number"],
        good_num,
    )
    try:
        id, name, description, cost = cur.fetchone()
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
            callback_data=f"ShowMerchChange_{good_num-1 if good_num != 1 else 1}",
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data=f"ShowMerchChange_{2 if category_size > good_num else 1}",
        ),
    )
    await state.set_data({"category_number": data["category_number"]})
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("BuyMerch_"))
async def buy_merch(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    merch_id = callback.data.split("_")[1]
    cur.execute("SELECT lucky FROM users WHERE chat_id = %s" % callback.message.chat.id)
    lucky = cur.fetchone()[0]
    cur.execute("SELECT name, cost FROM merch WHERE id = %s" % merch_id)
    name, needed_lucky = cur.fetchone()
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


@dp.callback_query(F.data.startswith("BuyMerchConfirm_"))
async def buy_merch_confirm(callback: CallbackQuery, state: State):
    merch_id = callback.data.split("_")[1]
    cur.execute(
        "SELECT lucky, id FROM users WHERE chat_id = %s" % callback.message.chat.id
    )
    lucky, user_id = cur.fetchone()
    cur.execute("SELECT name, cost FROM merch WHERE id = %s" % merch_id)
    name, needed_lucky = cur.fetchone()
    if needed_lucky > lucky:
        await callback.message.answer(
            "Вы не можете купить %s, у вас %s Lucky, а требуется %s"
            % (name, lucky, needed_lucky)
        )
        return
    cur.execute(
        """INSERT INTO orders (merch_id, user_id, cost)
VALUES (%s, %s, %s)"""
        % (merch_id, user_id, needed_lucky)
    )
    cur.execute(
        """
    UPDATE users SET lucky = lucky - %s WHERE id = %s"""
        % (needed_lucky, user_id)
    )
    con.commit()
    await callback.message.answer(
        f"Вы успешно заказали {name} за {needed_lucky} Lucky!\nС вами свяжутся. Советуем не удалять это сообщение."
    )


@dp.message(Command("/admin"))
async def admin_enter(message: Message, state: FSMContext):
    cur.execute(
        "SELECT user_id FROM users WHERE admin = 1 AND chat_id = {}".format(
            message.chat.id
        )
    )
    admin_found = bool(cur.fetchone()[0])
    if admin_found:
        await message.answer("Введите логин")
        await state.set_state(UserStates.login)


@dp.callback_query(F.data == "ShowUsers")
async def see_users(callback: CallbackQuery, state: FSMContext):
    # cur.execute(f"SELECT user_id FROM users WHERE chat_id = {callback.message.chat.id}")
    # user_id = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    users_num = cur.fetchone()[0]
    await state.set_data({"users_num": users_num})
    builder = InlineKeyboardBuilder()
    cur.execute(
        """
SELECT user_id,first_name,last_name,level,cash_online,lucky,another_value,admin,registered_at
FROM users LIMIT {} OFFSET 0""".format(
            users_per_page
        )
    )
    results = cur.fetchall()
    out_results = "Клиенты 1-{} из {}\n\n".format(len(results), users_num)
    for idx, trans in enumerate(results):
        idx += 1
        (
            user_id,
            first_name,
            last_name,
            level,
            cash_online,
            lucky,
            another_value,
            admin,
            registered_at,
        ) = trans
        builder.add(
            InlineKeyboardButton(text=str(idx), callback_data="User_" + str(user_id))
        )
        out_results += "{}. {} {} {}. Уровень: {}. Валюты: Cash: {}. Lucky: {}. Другая валюта: {}. Зарегистрирован: {}.\n".format(
            idx,
            "Админ." if admin else "",
            last_name,
            first_name,
            level,
            cash_online,
            lucky,
            another_value,
            registered_at,
        )
    builder.row(
        InlineKeyboardButton(text="⬅", callback_data="UsersPageChange_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="UsersPageChange_{}".format(
                1 if users_num < len(results) else 0
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("UsersPageChange_"))
async def see_users_change_page(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    page = int(callback.data.split("_")[1])
    await state.set_data(data)
    builder = InlineKeyboardBuilder()
    cur.execute(
        """
SELECT user_id,first_name,last_name,level,cash_online,lucky,another_value,admin,registered_at
FROM users LIMIT {} OFFSET 0""".format(
            users_per_page
        )
    )
    results = cur.fetchall()
    out_results = "Клиенты 1-{} из {}\n\n".format(len(results), data["users_num"])
    for idx, trans in enumerate(results):
        idx += 1
        (
            user_id,
            first_name,
            last_name,
            level,
            cash_online,
            lucky,
            another_value,
            admin,
            registered_at,
        ) = trans
        builder.add(
            InlineKeyboardButton(text=str(idx), callback_data="User_" + str(user_id))
        )
        out_results += "{}. {} {} {}. Уровень: {}. Валюты: Cash: {}. Lucky: {}. Другая валюта: {}. Зарегистрирован: {}.\n".format(
            idx,
            "Админ." if admin else "",
            last_name,
            first_name,
            level,
            cash_online,
            lucky,
            another_value,
            registered_at,
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅",
            callback_data="TransactionPageChange_{}".format(
                page - 1 if page != 0 else 0
            ),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                page + 1 if data["users_num"] < len(results) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("User_"))
async def see_user_detailed(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    id = callback.data.split("_")[1]
    builder.add(
        InlineKeyboardButton(
            text="Изменить имя и фамилию", callback_data="Change-Name-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить уровень", callback_data="Change-Level-%s" % id
        )
    )

    builder.add(
        InlineKeyboardButton(
            text="Поменять никнейм в телеграме", callback_data="Change-Username-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(text="Начислить Lucky", callback_data="Add-Lucky-%s" % id)
    )
    builder.add(
        InlineKeyboardButton(
            text="Начислить Cash Online", callback_data="Add-Cash_Online-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Начислить Другую валюту", callback_data="Add-Another_Value-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Снять Lucky", callback_data="Substract-Lucky-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Снять Cash Online", callback_data="Substract-Cash_Online-%s" % id
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Снять Другую валюту", callback_data="Substract-Another_Value-%s" % id
        )
    )
    cur.execute(
        f"SELECT user_id,chat_id,first_name,last_name,level,username,cash_online,lucky,another_value,admin,registered_at FROM users WHERE user_id = {id}"
    )
    (
        user_id,
        chat_id,
        first_name,
        last_name,
        level,
        username,
        cash_online,
        lucky,
        another_value,
        admin,
        registered_at,
    ) = cur.fetchone()
    answer = """
ID пользователя: {}.
ID чата с ботом {}.
Имя фамилия: {} {}.
Никнейм в телеграме: @{}.
Уроовень: {}.
Монеты:
Lucky: {}.
Cash Online: {}.
Другая валюта: {}.
{}Зарегистрирован: {}.
""".format(
        user_id,
        chat_id,
        first_name,
        last_name,
        username,
        level,
        lucky,
        cash_online,
        another_value,
        "Администратор.\n" if admin else "",
        registered_at,
    )
    builder.adjust(2)
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("Add-"))
async def add_money(callback: CallbackQuery, state: FSMContext):
    _, currency, id = callback.data.split("-")
    cur.execute("SELECT last_name, first_name FROM users WHERE user_id = {}".format(id))
    last_name, first_name = cur.fetchone()
    await callback.message.answer(
        "Введите, сколько {} Вы хотите начислить пользователю {} {}.".format(
            currency.replace("_", " "), last_name, first_name
        )
    )
    await state.set_data(
        {
            "user_id": id,
            "currency": currency.replace("_", " "),
            "first_name": first_name,
            "last_name": last_name,
        }
    )
    await state.set_state(UserStates.add_money)


@dp.message(UserStates.add_money)
async def enter_add_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    amount = int(search.group())
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmAddMoney")
    )
    data = await state.get_data()
    await state.set_data({"amount": amount, **data})
    await message.answer(
        "Начислить {} {} клиенту {} {}?".format(
            amount, data["currency"], data["last_name"], data["first_name"]
        ),
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmAddMoney")
async def confirm_add_money(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sql_currency = data["currency"].replace(" ", "_").lower()
    cur.execute(
        "UPDATE users SET {} = {} + {} WHERE user_id = {}".format(
            sql_currency, sql_currency, data["amount"], data["user_id"]
        )
    )
    cur.execute(
        "SELECT user_id FROM users WHERE chat_id = {}".format(callback.message.chat.id)
    )
    admin_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO transactions (trans_type, first_amount, from_user, to_user, first_currency)
        VALUES (4, {}, {}, {}, {})""".format(
            data["amount"],
            admin_id,
            data["user_id"],
            currencies_reverse[data["currency"]],
        )
    )
    con.commit()
    await callback.message.answer(
        "Вы успешно начислили {} {} пользователю {} {}".format(
            data["amount"], data["currency"], data["last_name"], data["first_name"]
        )
    )


@dp.callback_query(F.data.startswith("Substract-"))
async def substract_money(callback: CallbackQuery, state: FSMContext):
    _, currency, id = callback.data.split("-")
    cur.execute("SELECT last_name, first_name FROM users WHERE user_id = {}".format(id))
    last_name, first_name = cur.fetchone()
    await callback.message.answer(
        "Введите, сколько {} Вы хотите снять у пользователя {} {}.".format(
            currency.replace("_", " "), last_name, first_name
        )
    )
    await state.set_data(
        {
            "user_id": id,
            "currency": currency.replace("_", " "),
            "first_name": first_name,
            "last_name": last_name,
        }
    )
    await state.set_state(UserStates.substract_money)


@dp.message(UserStates.substract_money)
async def enter_substract_money(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    amount = int(search.group())
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmSubstractMoney")
    )
    data = await state.get_data()
    await state.set_data({"amount": amount, **data})
    await message.answer(
        "Снять {} {} у клиента {} {}?".format(
            amount, data["currency"], data["last_name"], data["first_name"]
        ),
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmSubstractMoney")
async def confirm_substract_money(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sql_currency = data["currency"].replace(" ", "_").lower()
    cur.execute(
        "UPDATE users SET {} = {} - {} WHERE user_id = {}".format(
            sql_currency, sql_currency, data["amount"], data["user_id"]
        )
    )
    cur.execute(
        "SELECT user_id FROM users WHERE chat_id = {}".format(callback.message.chat.id)
    )
    admin_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO transactions (trans_type, first_amount, from_user, to_user, first_currency)
        VALUES (5, {}, {}, {}, {})""".format(
            data["amount"],
            admin_id,
            data["user_id"],
            currencies_reverse[data["currency"]],
        )
    )
    con.commit()
    await callback.message.answer(
        "Вы успешно сняли {} {} у пользователя {} {}".format(
            data["amount"], data["currency"], data["last_name"], data["first_name"]
        )
    )


@dp.callback_query(F.data.startswith("Change-"))
async def change_user_value(callback: CallbackQuery, state: FSMContext):
    _, change_value, id = callback.data.split("-")
    cur.execute(
        "SELECT last_name, first_name, level, username FROM users WHERE user_id = {}".format(
            id
        )
    )
    last_name, first_name, level, username = cur.fetchone()
    match change_value:
        case "Name":
            await callback.message.answer(
                "Введите имя и фамилию на которые хотите поменять имя и фамилию пользователя"
            )
        case "Level":
            await callback.message.answer(
                "Введите число уровня на которое хотите поменять уровень пользователя"
            )
        case "Username":
            await callback.message.answer(
                """
Введите @никнейм в телеграме, на который нужно поменять никнейм пользователя.
Нельзя менять этот параметр просто так, только в случае багов."""
            )
    await state.set_data(
        {
            "user_id": id,
            "change_value": change_value,
            "first_name": first_name,
            "last_name": last_name,
            "level": level,
            "username": username,
        }
    )
    await state.set_state(UserStates.change_user_value)


@dp.message(UserStates.change_user_value)
async def enter_change_user_value(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    data = await state.get_data()
    match data["change_value"]:
        case "Name":
            if len(message.text.split(" ")) != 2:
                await message.answer("Введите имя и фамилию через пробел")
                return
            result = message.text.split(" ")
        case "Level":
            search = re.search("\d+", message.text)
            if not search:
                await message.answer(
                    text="Введите число", reply_markup=builder.as_markup()
                )
                return
            result = int(search.group())
        case "Username":
            result = message.text.split("")[0]
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmChangeUserValue")
    )
    match data["change_value"]:
        case "Name":
            first_name, last_name = result
            await message.answer(
                "Вы хотите поменять имя и фамилию пользователя {} {} на {} {}?".format(
                    data["first_name"], data["last_name"], first_name, last_name
                ),
                reply_markup=builder.as_markup(),
            )
        case "Level":
            await message.answer(
                "Вы хотите изменить уровень пользователя {} {} c {} на {}?".format(
                    data["last_name"], data["first_name"], data["level"], result
                ),
                reply_markup=builder.as_markup(),
            )
        case "Username":
            await message.answer(
                "Точно нужно изменить никнейм пользователя {} {} с {} на {}?".format(
                    data["last_name"], data["first_name"], data["username"], result
                ),
                reply_markup=builder.as_markup(),
            )
    await state.set_data({"result": result, **data})


@dp.callback_query(F.data == "ConfirmChangeUserValue")
async def confirm_change_user_value(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    match data["change_value"]:
        case "Name":
            new_first_name, new_last_name = data["result"]
            cur.execute(
                """
UPDATE users SET first_name = "{}", last_name = "{}" WHERE user_id = {}
""".format(
                    new_first_name, new_last_name, data["user_id"]
                )
            )
            await callback.message.answer(
                "Вы успешно сменили имя и фамилию пользователя с {} {} на {} {}.".format(
                    data["first_name"], data["last_name"], new_first_name, new_last_name
                )
            )
        case "Level":
            cur.execute(
                """
UPDATE users SET level = {} WHERE user_id = {}
""".format(
                    data["result"], data["user_id"]
                )
            )
            await callback.message.answer(
                "Вы успешно изменили уровень пользователя {} {} c {} на {}.".format(
                    data["last_name"], data["first_name"], data["level"], data["result"]
                )
            )
        case "Username":
            cur.execute(
                """
UPDATE users SET username = "{}" WHERE user_id = {}
""".format(
                    data["result"], data["user_id"]
                )
            )
            await callback.message.answer(
                "Вы успешно изменили никнейм пользователя {} {} с {} на {}.".format(
                    data["last_name"],
                    data["first_name"],
                    data["username"],
                    data["result"],
                )
            )
    con.commit()


@dp.callback_query(F.data == "ShowTransactionsAdmin")
async def see_transactions_admin(callback: CallbackQuery, state: FSMContext):
    cur.execute("SELECT COUNT(*) FROM transactions")
    trans_num = cur.fetchone()[0]
    await state.set_data({"trns_num": trans_num})
    builder = InlineKeyboardBuilder()
    cur.execute(
        f"""
        SELECT id, trans_type, first_amount, first_currency, second_amount, second_currency, from_user, to_user, what_bought, made_in FROM transactions
LIMIT {transactions_per_page} OFFSET 0"""
    )
    results = cur.fetchall()
    if not results:
        await bot.answer_callback_query(callback.id, "Транзакции отсутствуют")
        builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
        await callback.message.answer(
            text="Транзакции отсутствуют", reply_markup=builder.as_markup()
        )
        return
    out_results = "Транзакции 1-{} из {}\n\n".format(len(results), trans_num)
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
        cur.execute(
            "SELECT last_name, first_name FROM users WHERE user_id = %s" % from_user
        )
        last_name, first_name = cur.fetchone()
        match trans_type:
            case 0:
                out_results += "{}. {} {}. Обмен валют. Из {} {} в {} {}. {}\n".format(
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
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
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
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
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
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
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
        InlineKeyboardButton(text="⬅", callback_data="TransactionPageChangeAdmin_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChangeAdmin_{}".format(
                1 if trans_num < len(results) else 0
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("TransactionPageChangeAdmin_"))
async def see_transaction_change_page_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    page = int(callback.data.split("_")[1])
    await state.set_data(data)
    builder = InlineKeyboardBuilder()
    cur.execute(
        f"""
        SELECT id, trans_type, first_amount, first_currency, second_amount, second_currency, from_user, to_user, what_bought, made_in FROM transactions
LIMIT {transactions_per_page} OFFSET {transactions_per_page*page}"""
    )
    results = cur.fetchall()
    if not results:
        await bot.answer_callback_query(callback.id, "Пусто")
        return
    out_results = "Транзакции {}-{} из {}\n\n".format(
        1 + 10 * page, len(results) + 10 * page, data["trns_num"]
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
        last_name, first_name = cur.fetchone()
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
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
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
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
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
                cur.execute(
                    "SELECT last_name, first_name FROM users WHERE user_id = %s"
                    % to_user
                )
                to_user_last_name, to_user_first_name = cur.fetchone()
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
            callback_data="TransactionPageChangeAdmin_{}".format(
                page - 1 if page != 0 else 0
            ),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChangeAdmin_{}".format(
                page + 1 if data["trns_num"] < len(results) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data == "ShowMerchAdmin")
async def see_merch_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=category,
                callback_data=f"ShowMerchAdminCategory_{categories.index(category)}",
            )
        )
    builder.add(
        InlineKeyboardButton(
            text="Без категории", callback_data="ShowMerchAdminNoCategory"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Добавить категорию", callback_data="AddMerchItemCategory"
        )
    )
    builder.adjust(1, 2)
    await callback.message.answer(
        "Выберите категорию:", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("ShowMerchAdminCategory_"))
async def see_merch_admin_category(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(
            text="Выбрать другую категорию", callback_data="ShowMerchAdmin"
        )
    )
    category_number = int(callback.data.split("_")[1])
    cur.execute(f"SELECT COUNT(*) FROM merch WHERE category = {category_number}")
    category_size = int(cur.fetchone()[0])
    cur.execute(
        f"SELECT id, name, description, cost FROM merch WHERE category = {category_number} LIMIT 1 OFFSET 0"
    )
    try:
        id, name, description, cost = cur.fetchone()
    except:
        await callback.message.answer(
            "Категория пуста.", reply_markup=builder.as_markup()
        )
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить фотографию", callback_data=f"MerchChange_Photo_{id}"
        )
    )
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer(
            "Фотография пуста пуста.", reply_markup=builder.as_markup()
        )
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить категорию", callback_data=f"MerchChange_Category_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить цену", callback_data=f"MerchChange_Cost_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить название", callback_data=f"MerchChange_Name_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить описание", callback_data=f"MerchChange_Description_{id}"
        )
    )
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
        InlineKeyboardButton(text="⬅", callback_data="ShowMerchCategoryChange_1"),
        InlineKeyboardButton(
            text="➡",
            callback_data="ShowMerchAdminCategoryChange_{}".format(
                2 if category_size > 1 else 1
            ),
        ),
    )
    await state.set_data({"category_number": category_number})
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("ShowMerchCategoryChange_"))
async def see_merch_admin_category_change(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(
            text="Выбрать другую категорию", callback_data="ShowMerchAdmin"
        )
    )
    data = await state.get_data()
    good_num = int(callback.data.split("_")[1])
    cur.execute(
        "SELECT COUNT(*) FROM merch WHERE category = %s" % data["category_number"]
    )
    category_size = int(cur.fetchone()[0])
    cur.execute(
        "SELECT id, name, description, cost FROM merch WHERE category = %s LIMIT 1 OFFSET %s"
        % data["category_number"],
        good_num - 1,
    )
    try:
        id, name, description, cost = cur.fetchone()
    except:
        await callback.message.answer(
            "Категория пуста.", reply_markup=builder.as_markup()
        )
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить фотографию", callback_data=f"MerchChange_Photo_{id}"
        )
    )
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer(
            "Фотография отсутствует.", reply_markup=builder.as_markup()
        )
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить категорию", callback_data=f"MerchChange_Category_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить цену", callback_data=f"MerchChange_Cost_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить название", callback_data=f"MerchChange_Name_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить описание", callback_data=f"MerchChange_Description_{id}"
        )
    )
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
            callback_data=f"ShowMerchAdminCategoryChange_{good_num - 1 if good_num != 0 else 1}",
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data=f"ShowMerchAdminCategoryChange_{good_num + 1 if category_size > good_num+1 else good_num}",
        ),
    )
    await state.set_data({"category_number": data["category_number"]})
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "ShowMerchAdminNoCategory")
async def see_merch_admin_no_category(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(
            text="Выбрать другую категорию", callback_data="ShowMerchAdmin"
        )
    )
    cur.execute(f"SELECT COUNT(*) FROM merch")
    size = int(cur.fetchone()[0])
    cur.execute(
        f"SELECT id, name, description, cost, category FROM merch LIMIT 1 OFFSET 0"
    )
    try:
        id, name, description, cost, category = cur.fetchone()
    except:
        await callback.message.answer("Мерч пуст.", reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить фотографию", callback_data=f"MerchChange_Photo_{id}"
        )
    )
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer(
            "Фотография пуста пуста.", reply_markup=builder.as_markup()
        )
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить категорию", callback_data=f"MerchChange_Category_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить цену", callback_data=f"MerchChange_Cost_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить название", callback_data=f"MerchChange_Name_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить описание", callback_data=f"MerchChange_Description_{id}"
        )
    )
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
        InlineKeyboardButton(text="⬅", callback_data="ShowMerchNoCategoryChange_1"),
        InlineKeyboardButton(
            text="➡",
            callback_data="ShowMerchAdminNoCategoryChange_{}".format(
                2 if size > 1 else 1
            ),
        ),
    )
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("ShowMerchNoCategoryChange_"))
async def see_merch_admin_no_category_change(
    callback: CallbackQuery, state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    builder.add(
        InlineKeyboardButton(
            text="Выбрать другую категорию", callback_data="ShowMerchAdmin"
        )
    )
    good_num = int(callback.data.split("_")[1])
    cur.execute("SELECT COUNT(*) FROM merch")
    size = int(cur.fetchone()[0])
    cur.execute(
        "SELECT id, name, description, cost, category FROM merch LIMIT 1 OFFSET %s"
        % good_num
        - 1,
    )
    try:
        id, name, description, cost, category = cur.fetchone()
    except:
        await callback.message.answer("Мерч пуст.", reply_markup=builder.as_markup())
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить фотографию", callback_data=f"MerchChange_Photo_{id}"
        )
    )
    try:
        image = FSInputFile(f"merch_imgs/{id}.png")
    except:
        await callback.message.answer(
            "Фотография отсутствует.", reply_markup=builder.as_markup()
        )
        return
    builder.add(
        InlineKeyboardButton(
            text="Изменить категорию", callback_data=f"MerchChange_Category_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить цену", callback_data=f"MerchChange_Cost_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить название", callback_data=f"MerchChange_Name_{id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Изменить описание", callback_data=f"MerchChange_Description_{id}"
        )
    )
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
            callback_data=f"ShowMerchAdminNoCategoryChange_{good_num - 1 if good_num != 0 else 1}",
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data=f"ShowMerchAdminNoCategoryChange_{good_num + 1 if size > good_num+1 else good_num}",
        ),
    )
    await callback.message.answer_photo(
        photo=image, caption=answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "AddMerchItem")
async def add_merch_item_category(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
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


@dp.callback_query(F.data.startswith("AddMerchItemCategory_"))
async def add_merch_item_name(callback: CallbackQuery, state: FSMContext):
    category_number = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Напишите название товара", reply_markup=builder.as_markup()
    )
    await state.set_data({"category_number": category_number})
    await state.set_state(UserStates.create_merch_name)


@dp.message(UserStates.create_merch_name)
async def add_merch_item_cost(message: Message, state: FSMContext):
    data = await state.get_data()
    name = message.text
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    await message.answer("Напишите цену товара", reply_markup=builder.as_markup())
    await state.set_data({"name": name, **data})
    await state.set_state(UserStates.create_merch_cost)


@dp.message(UserStates.create_merch_cost)
async def add_merch_item_description(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    data = await state.get_data()
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    cost = int(search.group())
    await message.answer("Напишите описание товара", reply_markup=builder.as_markup())
    await state.set_data({"cost": cost, **data})
    await state.set_state(UserStates.create_merch_description)


@dp.message(UserStates.create_merch_description)
async def add_merch_item_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    description = message.text
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    await message.answer(
        "Пришлите фотографию для витрины", reply_markup=builder.as_markup()
    )
    await state.set_data({"description": description, **data})
    await state.set_state(UserStates.create_merch_photo)


@dp.message(F.photo and UserStates.create_merch_photo)
async def add_merch_item_photo_confirm(message: Message, state: FSMContext):
    print("ААА ЕДЯТ БЛЯТЬ")
    if not message.photo:
        print("Pizdec")
        return
    photo_id = message.photo[-1].file_id
    await bot.download(photo_id, "Merch_Item_Photo.png")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
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


@dp.callback_query(F.data == "AddMerchItemConfirm")
async def add_merch_item_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        return
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    cur.execute("SELECT id FROM merch ORDER BY id DESC LIMIT 1")
    if cur.fetchone() is None:
        last_id = 1
    else:
        last_id = cur.fetchone()[0]
    cur.execute(
        f"""
INSERT INTO merch (name, category, description, cost) 
VALUES ("{data["name"]}", {data["category_number"]}, "{data["description"]}", {data["cost"]})"""
    )
    os.replace("Merch_Item_Photo.png", f"merch_imgs/{last_id}.png")
    con.commit()
    await callback.message.answer(
        "Успешно добавлен товар {} за {}".format(data["name"], data["cost"]),
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data.startswith("MerchChange_"))
async def merch_change_property(callback: CallbackQuery, state: FSMContext):
    # Photo, Category, Cost, Name, Description
    _, property, id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    match property:
        case "Photo":
            await callback.message.answer(
                "Пришлите новое фото", reply_markup=builder.as_markup()
            )
        case "Category":
            for category in categories:
                builder.add(
                    InlineKeyboardButton(
                        text=category,
                        callback_data=f"MerchChangePropertyConfirm_{categories.index(category)}",
                    )
                )
            builder.adjust(1, 2)
            await callback.message.answer(
                "Выберите новую категорию", reply_markup=builder.as_markup()
            )
        case "Cost":
            await callback.message.answer(
                "Введите новую цену", reply_markup=builder.as_markup()
            )
        case "Name":
            await callback.message.answer(
                "Введите новое название", reply_markup=builder.as_markup()
            )
        case "Description":
            await callback.message.answer(
                "Введите новое описание", reply_markup=builder.as_markup()
            )
    await state.set_state(UserStates.merch_change_property)
    await state.set_data({"property": property, "id": id})


@dp.message(UserStates.merch_change_property)
async def merch_change_property_enter(message: Message, state: FSMContext):
    data = await state.get_data()
    property = data["property"]
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    match property:
        case "Photo":
            if not message.photo:
                await message.answer(
                    "Нужно прислать фото", reply_markup=builder.as_markup()
                )
            photo_id = message.photo[-1].file_id
            await bot.download(photo_id, "New_Merch_Photo.png")
        case "Cost":
            search = re.search("\d+", message.text)
            if not search:
                await message.answer(
                    text="Нужно ввести число", reply_markup=builder.as_markup()
                )
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
        InlineKeyboardButton(
            text="Подтвердить", callback_data="MerchChangePropertyConfirm"
        )
    )
    match property:
        case "Photo":
            await message.answer("Изменить фото?", reply_markup=builder.as_markup())
        case "Cost":
            await message.answer(
                f"Поменять цену на {value}?", reply_markup=builder.as_markup()
            )
        case "Name":
            await message.answer(
                f"Поменять название на {value}?", reply_markup=builder.as_markup()
            )
        case "Description":
            await message.answer(
                f"Поменять описание на {value}", reply_markup=builder.as_markup()
            )


@dp.callback_query(F.data.startswith("MerchChangePropertyConfirm"))
async def merch_change_property_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В админ панель", callback_data="Admin"))
    match data["property"]:
        case "Photo":
            os.replace("New_Merch_Photo.png", "merch_imgs/{}.png".format(data["id"]))
            photo = FSInputFile("merch_imgs/{}.png".format(data["id"]))
            await callback.message.answer_photo(
                photo,
                caption="Фото успешно изменено.",
                reply_markup=builder.as_markup(),
            )
        case "Category":
            category = callback.data.split("_")[1]
            cur.execute(
                "UPDATE merch SET category = {} WHERE id = {}".format(
                    category, data["id"]
                )
            )
            await callback.message.answer(
                f"Категория успешно изменена на {categories[int(category)]}",
                reply_markup=builder.as_markup(),
            )
        case "Cost":
            cur.execute(
                "UPDATE merch SET cost = {} WHERE id = {}".format(
                    data["value"], data["id"]
                )
            )
            await callback.message.answer(
                "Цена успешно изменена на {}".format(data["value"]),
                reply_markup=builder.as_markup(),
            )
        case "Name":
            cur.execute(
                """UPDATE merch SET name = "{}" WHERE id = {}""".format(
                    data["value"], data["id"]
                )
            )
            await callback.message.answer(
                "Название успешно изменено на {}".format(data["value"]),
                reply_markup=builder.as_markup(),
            )
        case "Description":
            cur.execute(
                """UPDATE merch SET description = "{}" WHERE id = {}""".format(
                    data["value"], data["id"]
                )
            )
            await callback.message.answer(
                "Описание успешно изменено на {}".format(data["value"]),
                reply_markup=builder.as_markup(),
            )
    con.commit()


@dp.callback_query(F.data == "AddMerchItemCategory")
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


@dp.callback_query(F.data == "AddMerchItemCategoryConfirm")
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


@dp.callback_query(F.data == "AddMerchItemCategoryConfirmConfirm")
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


@dp.callback_query(F.data == "AddMerchItemCategoryConfirmConfirmConfirm")
async def add_merch_category_confirm_confirm_confirm(
    callback: CallbackQuery, state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardBuilder(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Хорошо, введите название новой категории.", reply_markup=builder.as_markup()
    )
    await state.set_state(UserStates.add_merch_category)


@dp.message(UserStates.add_merch_category)
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


@dp.callback_query(F.data == "AddMerchCategory")
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
        f"Это ваша категория: {new_category}. Вы уверены, что точно хотите её добавить? Это последнее предупреждение. Если точно уверены, что хотите добавить эту категорию, не нажимайте перед этим никаких других кнопок и не пишите сообщений."
    )
    await state.set_data({"category": new_category})


@dp.callback_query(F.data == "AddMerchCategoryConfirm")
async def add_merch_category_total_confirm(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    new_category = (await state.get_data())["category"]
    categories.append(new_category)
    with open("categories.txt", "w") as f:
        f.write("")
    with open("categories.txt", "a") as f:
        for category in categories:
            f.write(category + "\n")
    await callback.message.answer(
        f"Вы успешно добавили категорию {new_category}!",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "EditQuizzesAdmin")
async def edit_quizzes_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    cur.execute("SELECT id, name, description, reward FROM quizzes")
    quizzes = cur.fetchall()
    answer = ""
    for id, quiz in enumerate(quizzes, start=1):
        quiz_id, name, description, reward = quiz
        answer += f"{id}. ID: {quiz_id}. Название: {name}. Описание: {description}. Вознаграждение: {reward}.\n"
        builder.add(
            InlineKeyboardButton(text=f"{id}", callback_data=f"EditQuizAdmin_{quiz_id}")
        )
    builder.row(
        InlineKeyboardButton(text="Добавить квиз", callback_data="AddQuizAdmin")
    )
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("EditQuizAdmin_"))
async def edit_quiz_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться", callback_data="EditQuizzesAdmin")
    )
    quiz_id = callback.data.split("_")[1]
    cur.execute(
        f"SELECT id, question, first_answer, second_answer, third_answer, fourth_answer, correct_answer FROM questions WHERE quiz_id = {quiz_id}"
    )
    questions = cur.fetchall()
    answer = ""
    for idx, question in enumerate(questions, start=1):
        id, question_text, *answers, correct_answer = question
        answer += f'{idx}. "{question_text}". \nОтветы: \n'
        for answ_id, answr in enumerate(answers, start=1):
            answer += f"{answ_id}. {answr}\n"
        answer += f"Верный ответ: {correct_answer}.\n"
        builder.add(
            InlineKeyboardButton(
                text=idx, callback_data=f"EditQuestion_{id}_Quiz_{quiz_id}"
            )
        )
    cur.execute(f"SELECT COUNT(*) FROM questions WHERE quiz_id = {quiz_id}")
    len_questions = cur.fetchone()[0]
    if len_questions < 20:
        builder.add(
            InlineKeyboardButton(
                text="Добавить вопрос", callback_data=f"AddQuestion_Quiz_{quiz_id}"
            )
        )
    builder.add(
        InlineKeyboardButton(text="Удалить квиз", callback_data=f"DeleteQuiz_{quiz_id}")
    )
    await callback.message.answer(
        "Выберите редактируемый вопрос: \n" + answer, reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("EditQuestion_"))
async def edit_question_in_quiz(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    _, question_id, _, quiz_id = callback.data.split("_")
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к квизу", callback_data=f"EditQuizAdmin_{quiz_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Редактировать вопрос",
            callback_data=f"EditQuestionQuestion_{question_id}_{quiz_id}",
        )
    )
    for idx in range(1, 5):
        builder.add(
            InlineKeyboardButton(
                text=f"Редактировать {idx} ответ",
                callback_data=f"EditAnswerQuestion_{question_id}_{quiz_id}_{idx}",
            )
        )
    builder.add(
        InlineKeyboardButton(
            text="Редактировать верный ответ",
            callback_data=f"EditCorrectAnswerQuestion_{question_id}_{quiz_id}",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Удалить вопрос", callback_data=f"DeleteQuizQuestion_{question_id}"
        )
    )
    builder.adjust(1)
    cur.execute(
        f"SELECT question, first_answer, second_answer, third_answer, fourth_answer, correct_answer FROM questions WHERE id = {question_id}"
    )
    question, *answers, correct_answer = cur.fetchone()
    answer_to = f"Вопрос: {question}\n Ответы:\n"
    for idx, answer in enumerate(answers, start=1):
        answer_to += f"{idx}. {answer}"
    answer_to += f"Верный ответ: {correct_answer}"
    await callback.message.answer(answer_to, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("EditQuestionQuestion"))
async def edit_question_question_in_quiz(callback: CallbackQuery, state: FSMContext):
    _, question_id, quiz_id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data=f"EditQuestion_{question_id}_Quiz_{quiz_id}",
        )
    )
    await state.set_state(UserStates.edit_question_question)
    await state.set_data({"question_id": question_id, "quiz_id": quiz_id})
    await callback.message.answer(
        "Введите новый текст вопроса", reply_markup=builder.as_markup()
    )


@dp.message(UserStates.edit_question_question)
async def edit_question_question_in_quiz_enter(message: Message, state: FSMContext):
    question_text = message.text
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data="EditQuestion_{}_Quiz_{}".format(
                data["question_id"], data["quiz_id"]
            ),
        )
    )
    cur.execute(
        f'UPDATE question SET question = "{question_text}" WHERE id = %s'
        % data["quiz_id"]
    )
    con.commit()
    await message.answer(f"Текст вопроса успешно изменен на {question_text}")


@dp.callback_query(F.data.startswith("EditAnswerQuestion"))
async def edit_answer_question_in_quiz(callback: CallbackQuery, state: FSMContext):
    _, question_id, quiz_id, answer_num = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data=f"EditQuestion_{question_id}_Quiz_{quiz_id}",
        )
    )
    await state.set_state(UserStates.edit_answer_question)
    await state.set_data(
        {"question_id": question_id, "quiz_id": quiz_id, "answer_num": answer_num}
    )
    await callback.message.answer(
        "Введите новый текст ответа", reply_markup=builder.as_markup()
    )


@dp.message(UserStates.edit_answer_question)
async def edit_answer_question_in_quiz_enter(message: Message, state: FSMContext):
    answer_text = message.text
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data="EditQuestion_{}_Quiz_{}".format(
                data["question_id"], data["quiz_id"]
            ),
        )
    )
    match int(data["answer_num"]):
        case 1:
            cur.execute(
                f'UPDATE question SET first_answer = "{answer_text}" WHERE id = %s'
                % data["quiz_id"]
            )
        case 2:
            cur.execute(
                f'UPDATE question SET second_answer = "{answer_text}" WHERE id = %s'
                % data["quiz_id"]
            )
        case 3:
            cur.execute(
                f'UPDATE question SET third_answer = "{answer_text}" WHERE id = %s'
                % data["quiz_id"]
            )
        case 4:
            cur.execute(
                f'UPDATE question SET fourth_answer = "{answer_text}" WHERE id = %s'
                % data["quiz_id"]
            )
    con.commit()
    await message.answer(f"Текст ответа успешно изменен на {answer_text}")


@dp.callback_query(F.data.startswith("EditCorrectAnswerQuestion"))
async def edit_correct_answer_question_in_quiz(
    callback: CallbackQuery, state: FSMContext
):
    _, question_id, quiz_id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data=f"EditQuestion_{question_id}_Quiz_{quiz_id}",
        )
    )
    await state.set_state(UserStates.edit_correct_answer_question)
    await state.set_data({"question_id": question_id, "quiz_id": quiz_id})
    await callback.message.answer(
        "Введите новый номер верного ответа", reply_markup=builder.as_markup()
    )


@dp.message(UserStates.edit_correct_answer_question)
async def edit_correct_answer_question_in_quiz_enter(
    message: Message, state: FSMContext
):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data="EditQuestion_{}_Quiz_{}".format(
                data["question_id"], data["quiz_id"]
            ),
        )
    )
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(
            text="Нужно ввести число", reply_markup=builder.as_markup()
        )
        return
    correct_answer = int(search.group())
    if correct_answer > 4 or correct_answer < 1:
        await message.answer(
            text="Число должно быть от 1 до 4, включительно",
            reply_markup=builder.as_markup(),
        )
        return
    cur.execute(
        f"UPDATE question SET correct_answer = {correct_answer} WHERE id = %s"
        % data["quiz_id"]
    )
    con.commit()
    await message.answer(f"Новый номер верного ответа изменён на {correct_answer}")


@dp.callback_query(F.data.startswith("AddQuestion_Quiz_"))
async def add_question_in_quiz(callback: CallbackQuery, state: FSMContext):
    _, _, quiz_id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в квизы", callback_data="EditQuizzesAdmin")
    )
    await state.set_data({"quiz_id": quiz_id})
    await state.set_state(UserStates.add_question_quiz)
    await callback.message.answer(
        """
Введите вопрос в таком формате:
[Текст вопроса][Первый вариант ответа][Второй вариант ответа][Третий вариант ответа][Четвёртый вариант ответа][Номер верного ответа]
Пример: [Когда Наполеон начал войну][1582г.][1917г.][1812г.][1783г.][3]
Если передумали добавлять вопрос, вернитесь в квизы""",
        reply_markup=builder.as_markup(),
    )


@dp.message(UserStates.add_question_quiz)
async def add_question_quiz_confirm(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в квизы", callback_data="EditQuizzesAdmin")
    )
    data = await state.get_data()
    if message.text.count("[") != 6 or message.text.count("]") != 6:
        await message.answer(
            """
Введите вопрос в таком формате:
[Текст вопроса][Первый вариант ответа][Второй вариант ответа][Третий вариант ответа][Четвёртый вариант ответа][Номер верного ответа]
Пример: [Когда Наполеон начал войну?][1582г.][1917г.][1812г.][1783г.][3]
Если передумали добавлять вопрос, вернитесь в квизы.""",
            reply_markup=builder.as_markup(),
        )
        await state.set_data({**data})
        await state.set_state(UserStates.add_question_quiz)
        return
    if not data["quiz_id"]:
        await message.answer(
            "Вернитесь в квиз и нажмите добавить вопрос снова.",
            reply_markup=builder.as_markup(),
        )
        return
    cur.execute(
        "SELECT COUNT(*) FROM questions WHERE quiz_id = {}".format(data["quiz_id"])
    )
    count = cur.fetchone()[0]
    if count > 19:
        await message.answer(
            "Этот квиз имеет максимальное количество вопросов",
            reply_markup=builder.as_markup(),
        )
        return
    text = list(
        map(lambda x: x.replace("[", "").replace("]", ""), message.text.split("]["))
    )
    (
        question_text,
        first_answer,
        second_answer,
        third_answer,
        fourth_answer,
        correct_answer,
    ) = text
    cur.execute(
        """INSERT INTO questions (question, first_answer, second_answer, third_answer, fourth_answer, correct_answer, quiz_id)
    VALUES ("{}", "{}", "{}", "{}", "{}", "{}", {})""".format(
            question_text,
            first_answer,
            second_answer,
            third_answer,
            fourth_answer,
            correct_answer,
            data["quiz_id"],
        )
    )
    con.commit()
    await message.answer(
        f"""
Вопрос принят!
Ваш вопрос: [{question_text}][{first_answer}][{second_answer}][{third_answer}][{fourth_answer}][{correct_answer}]
Если хотите закончить нажмите кнопку "Вернуться", а если хотите дальше продолжить писать вопросы, то
введите вопрос в таком формате:
[Текст вопроса][Первый вариант ответа][Второй вариант ответа][Третий вариант ответа][Четвёртый вариант ответа][Номер верного ответа]
Пример: [Когда Наполеон превратился в торт?][1582г.][1917г.][1812г.][2002г.][4]
Если передумали добавлять вопрос, вернитесь в квизы.""",
        reply_markup=builder.as_markup(),
    )
    await state.set_data({**data})
    await state.set_state(UserStates.add_question_quiz)


@dp.callback_query(F.data.startswith("DeleteQuizQuestion_"))
async def delete_quiz_question_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к квизам", callback_data="EditQuizzesAdmin"
        )
    )
    question_id = callback.data.split("_")[1]
    cur.execute(f"DELETE FROM questions WHERE id = {question_id}")
    con.commit()
    await callback.message.answer(
        "Вопрос успешно удалён!", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("DeleteQuiz_"))
async def delete_quiz_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к квизам", callback_data="EditQuizzesAdmin"
        )
    )
    quiz_id = callback.data.split("_")[1]
    cur.execute(f"DELETE FROM quizzes WHERE id = {quiz_id}")
    con.commit()
    await callback.message.answer(
        "Квиз успешно удалён!", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "AddQuizAdmin")
async def add_quiz_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="В список квизов", callback_data="EditQuizzesAdmin")
    )
    cur.execute("SELECT COUNT(*) FROM quizzes")
    count = cur.fetchone()[0]
    if count > 20:
        callback.message.answer(
            "Максимальное количество квизов, больше добавить нельзя",
            reply_markup=builder.as_markup(),
        )
    await callback.message.answer(
        """
Введите квиз полностью в одном сообщении в формате:
[Название][Описание][Награда]
Пример: [Квиз на то, получишь ли ты бабки][Здесь что-то про квиз, ну понятно][3 Lucky](Может быть Lucky, Cash Online или другая валюта, при награде в монетах ОБЯЗАТЕЛЬНО писать валюту!)
Наградой возможен мерч, если мерч, вписывать цифры его id, например [5] (Смотреть в просмотре мерча через панель админа)""",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(UserStates.add_quiz)


@dp.message(UserStates.add_quiz)
async def add_quiz_admin_enter(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="В список квизов", callback_data="EditQuizzesAdmin")
    )
    if message.text.count("[") != 3 or message.text.count("]") != 3:
        await message.answer(
            """
Введите квиз в таком формате:
[Название][Описание][Награда]
Пример: [Квиз на то, получишь ли ты бабки][Здесь что-то про квиз, ну понятно][3 Lucky](Может быть Lucky, Cash Online или другая валюта, при награде в монетах ОБЯЗАТЕЛЬНО писать валюту!)
Наградой возможен мерч, если мерч, вписывать цифры его id, например [5] (Смотреть в просмотре мерча через панель админа)""",
            reply_markup=builder.as_markup(),
        )
        await state.set_state(UserStates.add_question_quiz)
        return
    text = list(
        map(lambda x: x.replace("[", "").replace("]", ""), message.text.split("]["))
    )
    (name, description, reward) = text
    cur.execute(
        """INSERT INTO quizzes (name, description, reward) VALUES ("{}", "{}", "{}")""".format(
            name, description, reward
        )
    )
    con.commit()
    await message.answer(
        f"""
Квиз принят!
Ваш квиз: [{name}][{description}][{reward}]
Теперь добавьте вопросы.

Введите вопрос в таком формате:
[Текст вопроса][Первый вариант ответа][Второй вариант ответа][Третий вариант ответа][Четвёртый вариант ответа][Номер верного ответа]
Пример: [Когда Наполеон начал войну?][1582г.][1917г.][1812г.][1783г.][3]
Если передумали добавлять вопрос, вернитесь в квизы.""",
        reply_markup=builder.as_markup(),
    )
    cur.execute("SELECT id FROM quizzes WHERE name = '{name}'")
    quiz_id = cur.fetchone()[0]
    await state.set_data({"quiz_id": quiz_id})
    await state.set_state(UserStates.add_question_quiz)


@dp.callback_query(F.data.startswith("NotDeliveredMerch_"))
async def see_not_delivered_merch(callback: CallbackQuery, state: FSMContext):
    page = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    cur.execute(
        f"SELECT order_id, username, name, order_cost FROM (SELECT id as order_id, status, username, merch_id, cost as order_cost FROM orders JOIN users ON orders.user_id = users.user_id) JOIN merch ON merch_id = merch.id WHERE status = 0 LIMIT 10 OFFSET {page*10}"
    )
    orders = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 1")
    unanswered_orders = cur.fetchone()[0]
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


@dp.callback_query(F.data.startswith("DeliveredMerch_"))
async def see_delivered_merch(callback: CallbackQuery, state: FSMContext):
    page = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    cur.execute(
        f"SELECT order_id, username, name, order_cost FROM (SELECT id as order_id, status, username, merch_id, cost as order_cost FROM orders JOIN users ON orders.user_id = users.user_id) JOIN merch ON merch_id = merch.id WHERE status = 1 LIMIT 10 OFFSET {page*10}"
    )
    orders = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 1")
    answered_orders = cur.fetchone()[0]
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


@dp.callback_query(F.data.startswith("EditOrder_"))
async def edit_order_admin(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    cur.execute(
        """
    SELECT merch_id, name, cost, order_cost, first_name, last_name, orderer_id username, status, made_in
FROM (
    SELECT id, merch_id, first_name, last_name, username, users.user_id AS orderer_id, cost AS order_cost, status, made_in
    FROM orders
    JOIN users ON orders.user_id = users.user_id
) AS subquery
JOIN merch ON merch.id = subquery.merch_id WHERE subquery.id = {};
""".format(
            order_id
        )
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
    ) = cur.fetchone()
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


@dp.callback_query(F.data.startswith("EditOrderUnmarked"))
async def edit_order_unmarked(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    order_id = callback.data.split("_")[1]
    cur.execute("UPDATE orders SET status = 0 WHERE id = {}".format(order_id))
    con.commit()
    await callback.message.answer(
        "Статус успешно изменён на недоставленный.", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("EditOrderUnmarked"))
async def edit_order_unmarked(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    order_id = callback.data.split("_")[1]
    cur.execute("UPDATE orders SET status = 1 WHERE id = {}".format(order_id))
    con.commit()
    await callback.message.answer(
        "Статус успешно изменён на доставленный.", reply_markup=builder.as_markup()
    )


@dp.message(UserStates.login)
async def admin_login(message: Message, state: FSMContext):
    cur.execute(
        f"""
        SELECT password, powers FROM admins WHERE login = "{message.text}"
    """
    )
    admin = cur.fetchone()
    if not admin:
        await message.answer("Неверный логин")
        await state.clear()
        return
    await state.set_data({"admin": admin})
    await message.answer("Введите пароль")
    await state.set_state(UserStates.password)


@dp.message(UserStates.password)
async def admin_password(message: Message, state: FSMContext):
    data = await state.get_data()
    word, admin_level = data["admin"]  # , first_name, last_name = data["admin"]
    if message.text != word:
        await message.answer("Неверный пароль")
        await state.clear()
        return
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Войти в панель админа", callback_data="Admin")
    )
    await message.answer(
        f"Добро пожаловать, Баркалов Михаил. Ваш уровень админа: {admin_rights[admin_level]}",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "Admin")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    cur.execute(
        "SELECT admin FROM users WHERE chat_id = {}".format(callback.message.chat.id)
    )
    if not cur.fetchone()[0]:
        return
    builder = InlineKeyboardBuilder()
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
        InlineKeyboardButton(text="Добавить администратора", callback_data="Addmin")
    )
    builder.add(
        InlineKeyboardButton(text="Снять администратора", callback_data="SubAdmin")
    )
    builder.adjust(2)
    await callback.message.answer(
        f"Добро пожаловать, Баркалов Михаил. Ваш уровень админа: Главный разработчик",
        reply_markup=builder.as_markup(),
    )


@dp.message(F.photo)
async def scan_qr(message: Message, state: FSMContext):
    cur.execute(
        f"""
    SELECT admin FROM users WHERE chat_id = {message.chat.id}
    """
    )
    if not cur.fetchone()[0]:
        return
    photo_id = message.photo[-1].file_id
    await bot.download(photo_id, "Came_QR.png")
    inputImage = cv2.imread("Came_QR.png")
    qrDecoder = cv2.QRCodeDetector()
    data, _, _ = qrDecoder.detectAndDecode(inputImage)
    if len(data) <= 0:
        return  # QRCode не найден
    try:
        data = json.loads(data)
        data["type"]
    except:
        return
    match data["type"]:
        case "withdraw":
            cur.execute(
                """
SELECT status FROM withdraw_qrs WHERE id = %s"""
                % (data["qr_id"])
            )
            status = cur.fetchone()[0]
            if status == 1:
                await message.answer(
                    """
QRCode уже был активирован.
Чтобы вывести деньги снова, нужно получить новый QRCode."""
                )
                return
            elif status is None:
                await message.answer(
                    """
Такого QRCode`а не существует.
Возможна махинация."""
                )
                return
            cur.execute(
                "SELECT status FROM withdraw_qrs WHERE amount = %s AND id = %s"
                % (data["amount"], data["qr_id"])
            )
            status = cur.fetchone()[0]
            if status is None:
                await message.answer(
                    """
Сумма QRCode`а зарегистрированного по этому id не совпадает с текущим QRCode`ом.
Возможна махинация."""
                )
                return
            cur.execute(
                """
SELECT cash_online, first_name, last_name, username FROM users WHERE user_id = %s"""
                % data["user_id"]
            )
            available, first_name, last_name, username = cur.fetchone()
            if available < data["amount"]:
                await message.answer(
                    """
У клиента %s %s с никнеймом @%s недостаточно Cash Online.
У клиента на балансе %s Cash Online.
Клиент собирается вывести %s Cash Online."""
                    % (last_name, first_name, username, available, data["amount"])
                )
                return
            cur.execute(
                """
            UPDATE withdraw_qrs SET status = 1 WHERE id = %s"""
                % (data["qr_id"])
            )
            cur.execute(
                """
            INSERT INTO transactions (trans_type, from_user, first_amount, first_currency) VALUES (2, %s, %s, 1)"""
                % (data["user_id"], data["amount"])
            )
            con.commit()
            await message.answer(
                """
Клиент: %s %s, никнейм @%s.
Сумма: %s Cash Online."""
                % (last_name, first_name, username, data["amount"])
            )


@dp.message()
async def start(message: Message, state: FSMContext):
    cur.execute(
        f"""
        SELECT first_name, last_name FROM users WHERE chat_id = {message.chat.id}
    """
    )
    result = cur.fetchone()
    if not result:
        await state.set_state(UserStates.register)
        await message.answer(
            "Здравствуйте. Вы не зарегистрированы. Напишите имя и фамилию через пробел."
        )
        return
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    builder.add(InlineKeyboardButton(text="Подарки", callback_data="Gifts"))
    builder.add(InlineKeyboardButton(text="Мерч", callback_data="ShowMerch"))
    builder.adjust(1, 2)
    first_name, last_name = result
    await message.answer(
        f"Добрый день, {last_name} {first_name}!",
        reply_markup=builder.as_markup(),
    )


if __name__ == "__main__":
    el = asyncio.get_event_loop()
    el.run_until_complete(dp.start_polling(bot))
