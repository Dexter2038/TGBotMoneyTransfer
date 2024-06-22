from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import currencies
from app.utils import database
import segno

router = Router(name="user-transactions")


@router.callback_query(F.data == "Transactions")
async def transactions(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Просмотреть историю транзакций",
                             callback_data="ShowTransactions"))
    builder.add(
        InlineKeyboardButton(
            text="Показать историю транзакцию (QRCode)",
            callback_data="ShowQRTransactions",
        ))
    builder.adjust(1)
    await callback.message.answer(
        text=
        "Просмотреть историю транзакций здесь или получить QR-код, чтобы показать историю транзакций?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "ShowTransactions")
async def see_transactions(callback: CallbackQuery, state: FSMContext,
                           bot: Bot):
    user_id = database.get_user_id_by_chat_id(callback.message.chat.id)
    trans_num = database.get_transactions_len_by_user(user_id)
    await state.set_data({"user_id": user_id, "trns_num": trans_num})
    builder = InlineKeyboardBuilder()
    results = database.get_transactions_page(0, user_id)
    if not results:
        await bot.answer_callback_query(callback.id, "Транзакции отсутствуют")
        builder.add(
            InlineKeyboardButton(text="Профиль", callback_data="Profile"))
        await callback.message.answer(text="Транзакции отсутствуют",
                                      reply_markup=builder.as_markup())
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
            InlineKeyboardButton(text=str(idx),
                                 callback_data="Transaction_" + str(id)))
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
                from_user_last_name, from_user_first_name = (
                    database.get_name_by_user_id(from_user))
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".
                    format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        from_user_last_name,
                        from_user_first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    ))
            case 2:
                out_results += "{}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, first_amount, made_in)
            case 3:
                out_results += "{}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, what_bought, first_amount, made_in)
            case 4:
                from_user_last_name, from_user_first_name = (
                    database.get_name_by_user_id(from_user))
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
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
                from_user_last_name, from_user_first_name = (
                    database.get_name_by_user_id(from_user))
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
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
        InlineKeyboardButton(text="⬅",
                             callback_data="TransactionPageChange_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                1 if trans_num < len(results) else 0),
        ),
    )
    await callback.message.answer(out_results,
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("TransactionPageChange_"))
async def see_transaction_change_page(callback: CallbackQuery,
                                      state: FSMContext, bot: Bot):
    await callback.message.delete()
    data = await state.get_data()
    page = int(callback.data.split("_")[1])
    await state.set_data(data)
    builder = InlineKeyboardBuilder()
    results = database.get_transactions_page(page, data["user_id"])
    if not results:
        await bot.answer_callback_query(callback.id, "Пусто")
        return
    out_results = "Транзакции {}-{} из {}\n\n".format(1 + 10 * page,
                                                      len(results) + 10 * page,
                                                      data["trns_num"])
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
            InlineKeyboardButton(text=str(idx),
                                 callback_data="Transaction_" + str(id)))
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
                from_user_last_name, from_user_first_name = (
                    database.get_name_by_user_id(from_user))
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".
                    format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        from_user_last_name,
                        from_user_first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    ))
            case 2:
                out_results += "{}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, first_amount, made_in)
            case 3:
                out_results += "{}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, what_bought, first_amount, made_in)
            case 4:
                from_user_last_name, from_user_first_name = (
                    database.get_name_by_user_id(from_user))
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
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
                from_user_last_name, from_user_first_name = (
                    database.get_name_by_user_id(from_user))
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
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
            callback_data="TransactionPageChange_{}".format(page - 1 if page !=
                                                            0 else 0),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChange_{}".format(
                page + 1 if data["trns_num"] < len(results) +
                10 * page else page),
        ),
    )
    await callback.message.answer(out_results,
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("Transaction_"))
async def see_transaction_detailed(callback: CallbackQuery, state: FSMContext):
    id = callback.data.split("_")[1]
    data = database.get_transaction_data_by_id(id)
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
    ) = data
    match trans_type:
        case 0:
            from_user_last_name, from_user_first_name = database.get_name_by_user_id(
                from_user)
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
            from_user_last_name, from_user_first_name = database.get_name_by_user_id(
                from_user)
            to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                to_user)
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
            from_user_last_name, from_user_first_name = database.get_name_by_user_id(
                from_user)
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
            from_user_last_name, from_user_first_name = database.get_name_by_user_id(
                from_user)
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
            from_user_last_name, from_user_first_name = database.get_name_by_user_id(
                from_user)
            to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                to_user)
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
            from_user_last_name, from_user_first_name = database.get_name_by_user_id(
                from_user)
            to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                to_user)
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


@router.callback_query(F.data == "ShowQRTransactions")
async def show_transactions(callback: CallbackQuery, state: FSMContext):
    user_id = database.get_user_id_by_chat_id(callback.message.chat.id)
    message = '{"type" : "transactions","user_id" : %s}' % (user_id, )
    qr = segno.make_qr(message)
    qr.save("QR.png", scale=15)
    qr = FSInputFile("QR.png")
    await callback.message.answer_photo(
        qr,
        """
Предъявите QRCode нашему сотруднику.
Он его отсканирует.""",
    )
