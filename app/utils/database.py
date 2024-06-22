import sqlite3


def init():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    username VARCHAR(255) UNIQUE,
    level INT DEFAULT 1,
    xp INT DEFAULT 0,
    admin BOOLEAN DEFAULT FALSE,
    invite INT DEFAULT 0,
    referal VARCHAR(255),
    subscription BOOLEAN DEFAULT FALSE,
    lucky INT DEFAULT 0,
    cash_online INT DEFAULT 0,
    e_coin INT DEFAULT 0,
    registered_at DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime'))
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Quizzes (
    quiz_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    reward VARCHAR(255) NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Questions (
    question_id PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    question TEXT,
    first_answer TEXT,
    second_answer TEXT,
    third_answer TEXT,
    fourth_answer TEXT,
    correct_answer INTEGER,
    FOREIGN KEY (quiz_id) REFERENCES Quizzes(quiz_id) ON DELETE CASCADE
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS QuizPassed (
    user_id INTEGER NOT NULL,
    quiz_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES Quizzes(quiz_id) ON DELETE CASCADE
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS Merch (
    merch_id INTEGER PRIMARY KEY,
    category_number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cost INTEGER NOT NULL
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS Orders (
    order_id INTEGER PRIMARY KEY,
    merch_id INTEGER NOT NULL,
    order_status INT DEFAULT 0,
    user_id INT NOT NULL,
    order_cost INT NOT NULL,
    made_in DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')),
    FOREIGN KEY (merch_id) REFERENCES Merch(merch_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_type INT NOT NULL,
    from_user_id INT NOT NULL,
    to_user_id INT,
    from_amount INT NOT NULL,
    from_currency INT NOT NULL,
    to_amount INT,
    to_currency INT,
    created_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime'))
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS WithdrawQR (
    qr_id INT AUTO_INCREMENT PRIMARY KEY,
    amount INT NOT NULL,
    status INT DEFAULT 0
    )""")
    conn.commit()
    conn.close()


import sqlite3

database = sqlite3.connect('database.db')


def select_one(func):

    def wrapper(*args, **kwargs):
        cursor = database.cursor()
        cursor.execute(func(*args, *kwargs))
        return cursor.fetchone()[0]

    return wrapper


def select_many(func):

    def wrapper(*args, **kwargs):
        cursor = database.cursor()
        cursor.execute(func(*args, *kwargs))
        return cursor.fetchone()

    return wrapper


def select_all(func):

    def wrapper(*args, **kwargs):
        cursor = database.cursor()
        cursor.execute(func(*args, *kwargs))
        return cursor.fetchall()

    return wrapper


def update(func):

    def wrapper(*args, **kwargs):
        cursor = database.cursor()
        cursor.execute(func(*args, *kwargs))
        database.commit()

    return wrapper


def delete(func):

    def wrapper(*args, **kwargs):
        cursor = database.cursor()
        cursor.execute(func(*args, *kwargs))
        database.commit()

    return wrapper


def insert(func):

    def wrapper(*args, **kwargs):
        cursor = database.cursor()
        cursor.execute(func(*args, *kwargs))
        database.commit()
        return cursor.lastrowid

    return wrapper


@select_many
def get_user_name_level_username_by_user_id(id):
    return f"SELECT first_name, last_name, level, username FROM Users WHERE user_id = {id}"


@update
def set_user_name_by_user_id(new_first_name, new_last_name, user_id):
    return f"UPDATE Users SET first_name = '{new_first_name}', last_name = '{new_last_name}' WHERE user_id = {user_id}"


@update
def set_user_level_by_user_id(level, user_id):
    return f"UPDATE Users SET level = {level} WHERE user_id = {user_id}"


@update
def set_username_by_user_id(username, user_id):
    return f"UPDATE Users SET username = '{username}' WHERE user_id = {user_id}"


@update
def set_merch_parameter_value_by_id(parameter, value, id):
    return f"UPDATE Merch SET {parameter} = '{value}' WHERE merch_id = {id}"


@select_all
def get_quizzes_data():
    return "SELECT * FROM Quizzes"


@select_one
def get_quiestions_len_by_quiz_id(quiz_id):
    return f"SELECT COUNT(*) FROM Questions WHERE quiz_id = {quiz_id}"


@select_all
def get_questions_data_by_quiz_id(quiz_id):
    return f"SELECT * FROM Questions WHERE quiz_id = {quiz_id}"


@select_many
def get_question_by_id(question_id):
    return f"SELECT * FROM Questions WHERE question_id = {question_id}"


@update
def set_question_parameter_value_by_id(parameter, value, question_id):
    return f"UPDATE Questions SET {parameter} = '{value}' WHERE question_id = {question_id}"


@select_many
def get_profile_data_by_chat_id(chat_id):
    return f"SELECT first_name, level, cash_online, lucky, xp, e_coin FROM Users WHERE chat_id = {chat_id}"


@insert
def create_question(question_text, first_answer, second_answer, third_answer,
                    fourth_answer, correct_answer, quiz_id):
    return f"INSERT INTO Questions (question, first_answer, second_answer, third_answer, fourth_answer, correct_answer, quiz_id) VALUES ('{question_text}', '{first_answer}', '{second_answer}', '{third_answer}', '{fourth_answer}', {correct_answer}, {quiz_id})"


@delete
def delete_question_by_id(question_id):
    return f"DELETE FROM Questions WHERE question_id = {question_id}"


@delete
def delete_quiz_by_id(quiz_id):
    return f"DELETE FROM Quizzes WHERE quiz_id = {quiz_id}"


@select_one
def get_quizzes_len():
    return "SELECT COUNT(*) FROM Quizzes"


@insert
def create_quiz(name, description, reward):
    return f"INSERT INTO Quizzes (name, description, reward) VALUES ('{name}', '{description}', '{reward}')"


@select_many
def get_user_id_name_admin_by_username(username):
    return f"SELECT user_id, first_name, last_name, admin FROM Users WHERE username = '{username}'"


@select_many
def get_username_name_admin_by_user_id(user_id):
    return f"SELECT username, first_name, last_name, admin FROM Users WHERE user_id = {user_id}"


@update
def set_admin_status(status, user_id):
    return f"UPDATE Users SET admin = {status} WHERE user_id = {user_id}"


@select_many
def get_name_by_user_id(id):
    return f"SELECT last_name, first_name FROM Users WHERE user_id = {id}"


@update
def set_money_by_user_id(sign, sql_currency, amount, user_id):
    return f"UPDATE Users SET {sql_currency} = {sql_currency} {sign} {amount} WHERE user_id = {user_id}"


@select_one
def get_user_id_by_chat_id(chat_id):
    return f"SELECT user_id FROM Users WHERE chat_id = {chat_id}"


@insert
def create_transaction_transfer(transaction_type, from_user_id, to_user_id,
                                from_amount, from_currency):
    return f"INSERT INTO Transactions (transaction_type, from_user_id, to_user_id, from_amount, from_currency) VALUES ({transaction_type}, {from_user_id}, {to_user_id}, {from_amount}, {from_currency})"


@select_one
def get_admin_by_chat_id(chat_id):
    return f"SELECT COUNT(*) FROM Users WHERE chat_id = {chat_id} AND admin = 1"


@select_many
def get_withdraw_status_by_amount_and_id(qr_id, amount=None):
    if amount:
        return f"SELECT status FROM WithdrawQR WHERE qr_id = {qr_id} AND amount = {amount}"
    return f"SELECT status FROM WithdrawQR WHERE qr_id = {qr_id}"


@select_many
def get_cash_online_user_name_username_by_user_id(user_id):
    return f"SELECT cash_online, first_name, last_name, username FROM Users WHERE user_id = {user_id}"


@update
def set_withdraw_qr_status_by_id(qr_id):
    return f"UPDATE WithdrawQR SET status = 1 WHERE qr_id = {qr_id}"


@insert
def create_transaction_default(transaction_type, user_id, amount,
                               from_currency):
    return f"INSERT INTO Transactions (transaction_type, from_user_id, from_amount, from_currency) VALUES ({transaction_type}, {user_id}, {amount}, {from_currency})"


@select_one
def get_merch_len(category_number):
    return f"SELECT COUNT(*) FROM Merch WHERE category_number = {category_number}"


@select_many
def get_merch_item(category_number=None, offset=None):
    if category_number:
        if offset:
            return f"SELECT * FROM Merch WHERE category_number = {category_number} LIMIT 1 OFFSET {offset}"
        return f"SELECT * FROM Merch WHERE category_number = {category_number} LIMIT 1"
    if offset:
        return f"SELECT * FROM Merch LIMIT 1 OFFSET {offset}"
    return "SELECT * FROM Merch LIMIT 1"


@select_all
def get_delivering_merch_by_status(status, offset):
    return f"SELECT Merch.name, Merch.description, Merch.cost, Orders.order_id, Orders.order_cost, Orders.made_in, Users.first_name, Users.last_name, Users.username, Users.user_id FROM Merch INNER JOIN Orders ON Merch.merch_id = Orders.merch_id INNER JOIN Users ON Orders.user_id = Users.user_id WHERE Orders.order_status = {status} LIMIT 10 OFFSET {offset}"


@select_one
def get_orders_len_by_status(status):
    return f"SELECT COUNT(*) FROM Orders WHERE order_status = {status}"


@select_many
def get_merch_id_merch_name_merch_cost_order_cost_orderer_first_name_last_name_orderer_id_username_order_status_made_in_by_order_id(
        order_id):
    return f"SELECT Merch.merch_id, Merch.name, Merch.cost, Orders.order_cost, Users.first_name, Users.last_name, Users.user_id, Users.username, Orders.order_status, Orders.made_in FROM Merch INNER JOIN Orders ON Merch.merch_id = Orders.merch_id INNER JOIN Users ON Orders.user_id = Users.user_id WHERE Orders.order_id = {order_id}"


@update
def set_order_status(status, order_id):
    return f"UPDATE Orders SET order_status = {status} WHERE order_id = {order_id}"


@select_one
def get_transactions_len():
    return "SELECT COUNT(*) FROM Transactions"


@select_all
def get_transactions_page(page):
    return f"SELECT * FROM Transactions LIMIT 10 OFFSET {page * 10}"


@select_many
def get_name_by_user_id(user_id):
    return f"SELECT last_name, first_name FROM Users WHERE user_id = {user_id}"


@select_all
def get_transactions_page(page, user_id):
    return f"SELECT * FROM Transactions WHERE from_user_id = {user_id} OR to_user_id = {user_id} LIMIT 10 OFFSET {page * 10}"


@select_many
def get_transaction_data_by_id(id):
    return f"SELECT * FROM Transactions WHERE transaction_id = {id}"


@select_one
def get_admin_name_by_chat_id(chat_id):
    return f"SELECT first_name, last_name FROM Users WHERE chat_id = {chat_id} AND admin = 1"


@select_all
def get_chat_ids():
    return "SELECT chat_id FROM Users"


@update
def set_no_subscription_to_all():
    return "UPDATE Users SET subscription = 0"


@select_one
def get_chat_id_by_names(first_name, last_name):
    return f"SELECT chat_id FROM Users WHERE first_name = '{first_name}' AND last_name = '{last_name}'"


@select_one
def get_chat_id_by_username(username):
    return f"SELECT chat_id FROM Users WHERE username = '{username}'"


@select_one
def get_chat_id_by_user_id(id):
    return f"SELECT chat_id FROM Users WHERE user_id = {id}"


@select_many
def get_two_money_values_by_chat_id(chat_id):
    return f"SELECT cash_online, e_coin FROM Users WHERE chat_id = {chat_id}"


@select_many
def get_money_user_id_by_chat_id(currency, chat_id):
    return f"SELECT {currency}, user_id FROM Users WHERE chat_id = {chat_id}"


@update
def set_money_by_chat_id(sign, currency, amount, chat_id):
    return f"UPDATE Users SET {currency} = {currency} {sign} {amount} WHERE chat_id = {chat_id}"


@insert
def create_transaction_exchange(transaction_type, user_id, from_amount,
                                from_currency, to_amount, to_currency):
    return f"INSERT INTO Transactions (transaction_type, from_user_id, from_amount, from_currency, to_amount, to_currency) VALUES ({transaction_type}, {user_id}, {from_amount}, {from_currency}, {to_amount}, {to_currency})"


@select_many
def get_user_id_invited_status_by_chat_id(chat_id):
    return f"SELECT user_id, invite FROM Users WHERE chat_id = {chat_id}"


@select_many
def get_merch_id_name_cost_by_merch_id(merch_id):
    return f"SELECT merch_id, name, cost FROM Merch WHERE merch_id = {merch_id}"


@insert
def create_order(merch_id, order_cost, user_id):
    return f"INSERT INTO Orders (merch_id, order_cost, user_id) VALUES ({merch_id}, {order_cost}, {user_id})"


@update
def set_money_by_chat_id(sign, currency, amount, chat_id):
    return f"UPDATE Users SET {currency} = {currency} {sign} {amount} WHERE chat_id = {chat_id}"


@select_many
def get_user_id_subscribed_status_by_chat_id(chat_id):
    return f"SELECT user_id, subscription FROM Users WHERE chat_id = {chat_id}"


@select_one
def get_subscribed_status_by_chat_id(chat_id):
    return f"SELECT COUNT(*) FROM Users WHERE chat_id = {chat_id} AND subscription = 1"


@update
def set_yes_sunscription_to_chat_id(chat_id):
    return f"UPDATE Users SET subscription = 1 WHERE chat_id = {chat_id}"


@select_one
def get_lucky_by_chat_id(chat_id):
    return f"SELECT lucky FROM Users WHERE chat_id = {chat_id}"


@select_many
def get_merch_name_cost_by_merch_id(merch_id):
    return f"SELECT name, cost FROM Merch WHERE merch_id = {merch_id}"


@select_many
def get_lucky_id_level_xp_by_chat_id(chat_id):
    return f"SELECT lucky, level, xp FROM Users WHERE chat_id = {chat_id}"


@update
def set_xp_and_level_to_chat_id(xp, level, chat_id):
    return f"UPDATE Users SET xp = {xp}, level = {level} WHERE chat_id = {chat_id}"


@select_all
def get_quizzes_name_id():
    return "SELECT name, quiz_id FROM Quizzes"


@select_one
def get_quiz_passed_by_user_id(user_id, quiz_id):
    return f"SELECT COUNT(*) FROM QuizPassed WHERE user_id = {user_id} AND quiz_id = {quiz_id}"


@select_many
def get_quiz_name_desc_reward_by_id(id):
    return f"SELECT name, description, reward FROM Quizzes WHERE quiz_id = {id}"


@select_many
def get_question_data_by_num_and_quiz_id(question_num, quiz_id):
    return f"SELECT * FROM Questions WHERE quiz_id = {quiz_id} LIMIT 1 OFFSET {question_num - 1}"


@insert
def create_quiz_passed_field(user_id, quiz_id):
    return f"INSERT INTO QuizPassed (user_id, quiz_id) VALUES ({user_id}, {quiz_id})"


@select_one
def get_quiz_reward(quiz_id):
    return f"SELECT reward FROM Quizzes WHERE quiz_id = {quiz_id}"


@insert
def create_user(chat_id, first_name, last_name, username):
    return f"INSERT INTO Users (chat_id, first_name, last_name, username) VALUES ({chat_id}, '{first_name}', '{last_name}', '{username}')"


@select_many
def get_name_by_chat_id(chat_id):
    return f"SELECT first_name, last_name FROM Users WHERE chat_id = {chat_id}"


@select_one
def get_transactions_len_by_user(user_id):
    return f"SELECT COUNT(*) FROM Transactions WHERE from_user_id = {user_id} OR to_user_id = {user_id}"


@select_all
def get_transactions_page(page, user_id):
    return f"SELECT * FROM Transactions WHERE from_user_id = {user_id} OR to_user_id = {user_id} LIMIT 10 OFFSET {page * 10}"


@select_many
def get_user_name_user_id_by_username(username):
    return f"SELECT first_name, last_name, user_id FROM Users WHERE username = '{username}'"


@update
def set_money_by_username(sign, currency, amount, username):
    return f"UPDATE Users SET {currency} = {currency} {sign} {amount} WHERE username = '{username}'"


@insert
def create_transaction_transfer(transaction_type, from_user_id, to_user_id,
                                from_amount, from_currency):
    return f"INSERT INTO Transactions (transaction_type, from_user_id, to_user_id, from_amount, from_currency) VALUES ({transaction_type}, {from_user_id}, {to_user_id}, {from_amount}, {from_currency})"


@select_one
def get_money_by_chat_id(currency, chat_id):
    return f"SELECT {currency} FROM Users WHERE chat_id = {chat_id}"


@insert
def create_withdraw_qr(amount):
    return f"INSERT INTO WithdrawQR (amount) VALUES ({amount})"


@select_one
def get_last_merch_id():
    return "SELECT LAST_INSERT_ROWID()"


@insert
def create_merch(name, category_number, description, cost):
    return f"INSERT INTO Merch (name, category_number, description, cost) VALUES ('{name}', {category_number}, '{description}', {cost})"
