import asyncio
import datetime
import io
import logging
from os import getenv, environ

from aiogram import Bot, types, F, Dispatcher
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

config.Initializer()
transactions_per_page = 10
users_per_page = 10

currencies = {0: "Lucky", 1: "Cash Online", 2: "Another Value"}
currencies_reverse = {"Lucky": 0, "Cash Online": 1, "Another Value": 2}
transactions = {
    0: "Обмен валют",
    1: "Перевод",
    2: "Вывод монет",
    3: "Покупка",
    4: "Начисление от администратора",
    5: "Снятие от администратора",
}
admin_rights = {0: "Главный разработчик"}


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
    """
    CREATE TABLE IF NOT EXISTS withdraw_qrs(
    id INTEGER PRIMARY KEY,
    status INTEGER NOT NULL DEFAULT 0,
    amount INTEGET NOT NULL
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


@dp.message(F.photo)
async def scan_qr(message: types.Message, state: FSMContext):
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


@dp.message(UserStates.register)
async def register_user(message: types.Message, state: FSMContext):
    if len(message.text.split(" ")) != 2:
        await message.answer("Введите пожалуйста ваше имя и фамилию через пробел")
        await state.set_state(UserStates.register)
        return
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="В профиль", callback_data="Profile"))
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
async def profile(callback: types.CallbackQuery, state: FSMContext):
    cur.execute(
        f"""
        SELECT first_name, level, cash_online, lucky, another_value FROM users WHERE chat_id = {callback.message.chat.id}
    """
    )
    first_name, level, cash_online, lucky, another_value = cur.fetchone()
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="История транзакций", callback_data="Transactions"
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Обменять монеты", callback_data="ExchangeMoney"
        )
    )
    builder.add(
        types.InlineKeyboardButton(text="Передать монеты", callback_data="GiveMoney")
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Вывести Cash Online", callback_data="WithdrawMoney"
        )
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
async def transactions(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Просмотреть историю транзакций", callback_data="ShowTransactions"
        )
    )
    builder.add(
        types.InlineKeyboardButton(
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
async def see_transactions(callback: types.CallbackQuery, state: FSMContext):
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
        builder.add(types.InlineKeyboardButton(text="Профиль", callback_data="Profile"))
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
            types.InlineKeyboardButton(
                text=str(idx), callback_data="Transaction_" + str(id)
            )
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
                )
    builder.row(
        types.InlineKeyboardButton(text="⬅", callback_data="TransactionPageChange_0"),
        types.InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                1 if trans_num < len(results) else 0
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("TransactionPageChange_"))
async def see_transaction_change_page(callback: types.CallbackQuery, state: FSMContext):
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
            types.InlineKeyboardButton(
                text=str(idx), callback_data="Transaction_" + str(id)
            )
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
                )
    builder.row(
        types.InlineKeyboardButton(
            text="⬅",
            callback_data="TransactionPageChange_{}".format(
                page - 1 if page != 0 else 0
            ),
        ),
        types.InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                page + 1 if data["trns_num"] < len(results) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("Transaction_"))
async def see_transaction_detailed(callback: types.CallbackQuery, state: FSMContext):
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
async def show_transactions(callback: types.CallbackQuery, state: FSMContext):
    qr = segno.make_qr("Transaction completed in 12:20")
    qr.save("QR.png", scale=10)
    qr = types.FSInputFile("QR.png")
    await callback.message.answer_photo(qr, "QR код для пользователя тэтатэ")


@dp.callback_query(F.data == "ExchangeMoney")
async def exchange_money(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Обменять Lucky на Cash Online",
            callback_data="Exchange-LuckyToCash_Online",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Обменять Cash Online на Lucky",
            callback_data="Exchange-Cash_OnlineToLucky",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Обменять Lucky на Another Value",
            callback_data="Exchange-LuckyToAnother_Value",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Обменять Another Value на Lucky",
            callback_data="Exchange-Another_ValueToLucky",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Обменять Cash Online на Another Value",
            callback_data="Exchange-Cash_OnlineToAnother_Value",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Обменять Another Value на Cash Online",
            callback_data="Exchange-Another_ValueToCash_Online",
        )
    )
    await callback.message.answer(
        "Какую валюту на какую вы хотиsте обменять?", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("Exchange-"))
async def exchange_value_to_value(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Отменить", callback_data="ExchangeMoney")
    )
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
async def enter_exchange_value_to_value(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Вернуться", callback_data="ExchangeMoney")
    )
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
        types.InlineKeyboardButton(
            text="Подтвердить", callback_data="ConfirmExchangeValue"
        )
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
async def confirm_exchange_value_to_value(
    callback: types.CallbackQuery, state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Вернуться", callback_data="ExchangeMoney")
    )
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
async def give(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
    )
    builder.row(types.InlineKeyboardButton(text="Lucky", callback_data="Give-Lucky"))
    builder.row(
        types.InlineKeyboardButton(text="Cash Online", callback_data="Give-Cash_Online")
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Another Value", callback_data="Give-Another_Value"
        )
    )
    await callback.message.answer(
        "Какую валюту Вы хотите передать?", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("Give-"))
async def give_currency(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("-")[1]
    cur.execute(
        f"""
SELECT {currency.lower()} FROM users WHERE chat_id = {callback.message.chat.id}
"""
    )
    available = cur.fetchone()[0]
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
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
async def give_money(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
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
async def give_money_to_person(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
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
        types.InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmGiveMoney")
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
async def give_money_to_person_confirm(
    callback: types.CallbackQuery, state: FSMContext
):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
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
async def withdraw_money(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Вернуться в профиль", callback_data="Profile")
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
async def enter_withdraw_money(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Вернуться", callback_data="GiveMoney"))
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
        types.InlineKeyboardButton(
            text="Подтвердить", callback_data="ConfirmWithdrawMoney"
        )
    )
    await state.set_data({"amount": result})
    await message.answer(
        f"""
Вы хотите вывести {result} Cash Online?
    """,
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmWithdrawMoney")
async def confirm_withdraw_money(callback: types.CallbackQuery, state: FSMContext):
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
    qr = types.FSInputFile("QR.png")
    await callback.message.answer_photo(
        qr,
        """
Предъявите QRCode нашему сотруднику.
Он его отсканирует.""",
    )


@dp.callback_query(F.data == "Gifts")
async def gifts(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Подарочки")


@dp.callback_query(F.data == "Merch")
async def merch(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("""Тут наш мерч""")


@dp.message(Command("/admin"))
async def admin_enter(message: types.Message, state: FSMContext):
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
async def see_users(callback: types.CallbackQuery, state: FSMContext):
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
            types.InlineKeyboardButton(
                text=str(idx), callback_data="User_" + str(user_id)
            )
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
        types.InlineKeyboardButton(text="⬅", callback_data="UsersPageChange_0"),
        types.InlineKeyboardButton(
            text="➡",
            callback_data="UsersPageChange_{}".format(
                1 if users_num < len(results) else 0
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("UsersPageChange_"))
async def see_users_change_page(callback: types.CallbackQuery, state: FSMContext):
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
            types.InlineKeyboardButton(
                text=str(idx), callback_data="User_" + str(user_id)
            )
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
        types.InlineKeyboardButton(
            text="⬅",
            callback_data="TransactionPageChange_{}".format(
                page - 1 if page != 0 else 0
            ),
        ),
        types.InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                page + 1 if data["users_num"] < len(results) + 10 * page else page
            ),
        ),
    )
    await callback.message.answer(out_results, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("User_"))
async def see_user_detailed(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    id = callback.data.split("_")[1]
    builder.add(
        types.InlineKeyboardButton(
            text="Изменить имя и фамилию", callback_data="Change-Name-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Изменить уровень", callback_data="Change-Level-%s" % id
        )
    )

    builder.add(
        types.InlineKeyboardButton(
            text="Поменять никнейм в телеграме", callback_data="Change-Username-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Начислить Lucky", callback_data="Add-Lucky-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Начислить Cash Online", callback_data="Add-Cash_Online-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Начислить Другую валюту", callback_data="Add-Another_Value-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Снять Lucky", callback_data="Substract-Lucky-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Снять Cash Online", callback_data="Substract-Cash_Online-%s" % id
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Снять Другую валюту", callback_data="Substract-Another_Value-%s" % id
        )
    )
    cur.execute(
        f"SELECT user_id,chat_id,first_name,last_name,level,username,cash_online,lucky,another_value,admin,registered_at FROM users"
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
    builder.adjust(3, 3, 3)
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("Add-"))
async def add_money(callback: types.CallbackQuery, state: FSMContext):
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
async def enter_add_money(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    amount = int(search.group())
    builder.row(
        types.InlineKeyboardButton(text="Подтвердить", callback_data="ConfirmAddMoney")
    )
    data = await state.get_data()
    await state.set_data({"amount": amount}, **data)
    await message.answer(
        "Начислить {} {} клиенту {} {}?".format(
            amount, data["currency"], data["last_name"], data["first_name"]
        ),
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmAddMoney")
async def confirm_add_money(callback: types.CallbackQuery, state: FSMContext):
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


@dp.callback_query(F.data.startswith("Substract-"))
async def substract_money(callback: types.CallbackQuery, state: FSMContext):
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
async def enter_substract_money(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Вернуться", callback_data="Admin"))
    search = re.search("\d+", message.text)
    if not search:
        await message.answer(text="Введите число", reply_markup=builder.as_markup())
        return
    amount = int(search.group())
    builder.row(
        types.InlineKeyboardButton(
            text="Подтвердить", callback_data="ConfirmSubstractMoney"
        )
    )
    data = await state.get_data()
    await state.set_data({"amount": amount}, **data)
    await message.answer(
        "Снять {} {} у клиента {} {}?".format(
            amount, data["currency"], data["last_name"], data["first_name"]
        ),
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "ConfirmSubstractMoney")
async def confirm_substract_money(callback: types.CallbackQuery, state: FSMContext):
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


@dp.callback_query(F.data.startswith("Change-"))
async def change_user_value(callback: types.CallbackQuery, state: FSMContext):
    pass


@dp.message(UserStates.login)
async def admin_login(message: types.Message, state: FSMContext):
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
async def admin_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    word, admin_level = data["admin"]  # , first_name, last_name = data["admin"]
    if message.text != word:
        await message.answer("Неверный пароль")
        await state.clear()
        return
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Войти в панель админа", callback_data="Admin")
    )
    await message.answer(
        f"Добро пожаловать, Баркалов Михаил. Ваш уровень админа: {admin_rights[admin_level]}",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "Admin")
async def admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    cur.execute("SELECT admin FROM users WHERE chat_id = %s" % callback.message.chat.id)
    if not cur.fetchone()[0]:
        return
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Просмотреть пользователей", callback_data="ShowUsers"
        )
    )
    await callback.message.answer(
        f"Добро пожаловать, Баркалов Михаил. Ваш уровень админа: Главный разработчик",
        reply_markup=builder.as_markup(),
    )


@dp.message()
async def start(message: types.Message, state: FSMContext):
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
    builder.add(types.InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    builder.add(types.InlineKeyboardButton(text="Подарки", callback_data="Gifts"))
    builder.add(types.InlineKeyboardButton(text="Мерч", callback_data="Merch"))
    builder.adjust(1, 2)
    first_name, last_name = result
    await message.answer(
        f"Добрый день, {last_name} {first_name}, что пожелаете?",
        reply_markup=builder.as_markup(),
    )


if __name__ == "__main__":
    el = asyncio.get_event_loop()
    el.run_until_complete(dp.start_polling(bot))
