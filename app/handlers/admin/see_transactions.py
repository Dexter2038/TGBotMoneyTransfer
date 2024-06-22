from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils import database
from app.config import currencies

router = Router(name="admin-transactions-watch")


@router.callback_query(F.data == "ShowTransactionsAdmin")
async def see_transactions_admin(callback: CallbackQuery, state: FSMContext,
                                 bot: Bot):
    trans_num = database.get_transactions_len()
    await state.set_data({"trns_num": trans_num})
    builder = InlineKeyboardBuilder()
    results = database.get_transactions_page(0)
    if not results:
        await bot.answer_callback_query(callback.id, "Транзакции отсутствуют")
        builder.add(
            InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
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
        last_name, first_name = database.get_name_by_user_id(from_user)
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
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".
                    format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        last_name,
                        first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    ))
            case 2:
                out_results += "{}. {} {}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, last_name, first_name, first_amount, made_in)
            case 3:
                out_results += "{}. {} {}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, last_name, first_name, what_bought, first_amount,
                    made_in)
            case 4:
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
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
                    to_user)
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
        InlineKeyboardButton(text="⬅",
                             callback_data="TransactionPageChangeAdmin_0"),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChangeAdmin_{}".format(
                1 if trans_num < len(results) else 0),
        ),
    )
    await callback.message.answer(out_results,
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("TransactionPageChangeAdmin_"))
async def see_transaction_change_page_admin(callback: CallbackQuery,
                                            state: FSMContext, bot: Bot):
    await callback.message.delete()
    data = await state.get_data()
    page = int(callback.data.split("_")[1])
    await state.set_data(data)
    builder = InlineKeyboardBuilder()
    results = database.get_transactions_page(page)
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
        last_name, first_name = database.get_name_by_user_id(from_user)
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
                    to_user)
                out_results += (
                    "{}. Перевод {} {} от клиента {} {} клиенту {} {}. {}\n".
                    format(
                        idx,
                        first_amount,
                        currencies[first_currency],
                        last_name,
                        first_name,
                        to_user_last_name,
                        to_user_first_name,
                        made_in,
                    ))
            case 2:
                out_results += "{}. {} {}. Вывод Cash Online. Сумма: {}. {}\n".format(
                    idx, last_name, first_name, first_amount, made_in)
            case 3:
                out_results += "{}. {} {}. Покупка товара {} за {} Lucky. {}\n".format(
                    idx, last_name, first_name, what_bought, first_amount,
                    made_in)
            case 4:
                to_user_last_name, to_user_first_name = database.get_name_by_user_id(
                    to_user)
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
                    to_user)
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
                page - 1 if page != 0 else 0),
        ),
        InlineKeyboardButton(
            text="➡",
            callback_data="TransactionPageChangeAdmin_{}".format(
                page + 1 if data["trns_num"] < len(results) +
                10 * page else page),
        ),
    )
    await callback.message.answer(out_results,
                                  reply_markup=builder.as_markup())
