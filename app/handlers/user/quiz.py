from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils import database

router = Router(name="user-quiz")


@router.callback_query(F.data == "Quizzes")
async def show_quizzes(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    quizzes = database.get_quizzes_name_id()
    if not quizzes:
        await callback.message.answer("Квизы отсутствуют",
                                      reply_markup=builder.as_markup())
        return
    for name in quizzes:
        name, id = name
        builder.add(
            InlineKeyboardButton(text=name, callback_data="Quiz_%s" % id))
    builder.adjust(1, 6, 6, 6, 6)
    await callback.message.answer("Выберите квиз: ",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("Quiz_"))
async def show_quiz(callback: CallbackQuery, state: FSMContext):
    id = callback.data.split("_")[1]
    user_id = database.get_user_id_by_chat_id(callback.message.chat.id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    builder.row(InlineKeyboardButton(text="В квизы", callback_data="Quizzes"))
    if database.get_quiz_passed_by_user_id(user_id, id):
        await callback.message.answer(text="Вы уже проходили этот квиз.",
                                      reply_markup=builder.as_markup())
        return
    data = database.get_quiz_name_desc_reward_by_id(id)
    name, description, reward = data
    builder.add(
        InlineKeyboardButton(text="Далее",
                             callback_data="Question_0_Quiz_{}".format(id)))
    builder.adjust(2)
    await callback.message.answer(
        f"""
Тест {name}
{description}
Награда {reward}.
При прохождении, советуем не писать никаких других сообщений боту и не нажимать кнопки, чтобы всё засчиталось точно""",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("Question_"))
async def show_question(callback: CallbackQuery, state: FSMContext):
    _, question_num, _, quiz_id = callback.data.split("_")
    state_data = await state.get_data()
    rightanswers = state_data["right-answers"] if state_data else 0
    data = database.get_question_data_by_num_and_quiz_id(question_num, quiz_id)
    if not data:
        user_id = database.get_user_id_by_chat_id(callback.message.chat.id)
        database.create_quiz_passed_field(user_id, quiz_id)
        correct_answers = database.get_quiestions_len_by_quiz_id(quiz_id)
        if correct_answers == rightanswers:
            reward = database.get_quiz_reward(quiz_id)
            if reward.is_digit():
                data = database.get_merch_id_name_cost_by_merch_id(reward)
                merch_id, name, cost = data
                database.create_order(merch_id, 0, user_id)
                await callback.message.answer(
                    f"Вы выиграли мерч! {name} за {cost} БЕСПЛАТНО!")
            else:
                value = reward.split(" ")[0]
                reward_currency = reward.replace(f"{value} ", "")
                bd_reward_currency = reward_currency.replace(" ", "_").lower()
                database.set_money_by_chat_id("+", bd_reward_currency, value,
                                              callback.message.chat.id)
                await callback.message.answer(
                    f"Вы выиграли {value} {reward_currency}!")
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
                callback_data=
                f"Answer_{id+1}_{correct_answer}_Question_{question_num}_Quiz_{quiz_id}_{rightanswers}",
            ))
    await callback.message.answer(question, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("Answer_"))
async def check_question(callback: CallbackQuery, state: FSMContext):
    _, answer, correct_answer, _, question_num, _, quiz_id, right_answers = (
        callback.data.split("_"))
    if answer == correct_answer:
        await state.set_data({"right-answers": int(right_answers) + 1})
    else:
        await state.set_data({"right-answers": int(right_answers)})
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Дальше",
            callback_data=f"Question_{int(question_num)+1}_Quiz_{quiz_id}",
        ))
    await callback.message.answer("Дальше", reply_markup=builder.as_markup())
