from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states import AdminStates
from app.utils import database

import re

router = Router(name="admin-edit-quizzes")


@router.callback_query(F.data == "EditQuizzesAdmin")
async def edit_quizzes_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    quizzes = database.get_quizzes_data()
    builder.row(
        InlineKeyboardButton(text="Добавить квиз",
                             callback_data="AddQuizAdmin"))
    answer = ""
    if not quizzes:
        await callback.message.answer("Квизы отсутствуют",
                                      reply_markup=builder.as_markup())
        return
    for id, quiz in enumerate(quizzes, start=1):
        quiz_id, name, description, reward = quiz
        answer += (
            "{}. ID: {}. Название: {}. Описание: {}. Вознаграждение: {}.\n".
            format(
                id,
                quiz_id,
                name,
                description,
                "Мерч id {}".format(reward) if reward.isdigit() else reward,
            ))
        builder.add(
            InlineKeyboardButton(text=f"{id}",
                                 callback_data=f"EditQuizAdmin_{quiz_id}"))
    await callback.message.answer(answer, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("EditQuizAdmin_"))
async def edit_quiz_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться",
                             callback_data="EditQuizzesAdmin"))
    quiz_id = callback.data.split("_")[1]
    len_questions = database.get_quiestions_len_by_quiz_id(quiz_id)
    if len_questions < 16:
        builder.add(
            InlineKeyboardButton(text="Добавить вопрос",
                                 callback_data=f"AddQuestion_Quiz_{quiz_id}"))
    builder.add(
        InlineKeyboardButton(text="Удалить квиз",
                             callback_data=f"DeleteQuiz_{quiz_id}"))
    questions = database.get_questions_data_by_quiz_id(quiz_id)
    answer = ""
    for idx, question in enumerate(questions, start=1):
        id, question_text, *answers, correct_answer = question
        answer += f'{idx}. "{question_text}". \nОтветы: \n'
        for answ_id, answr in enumerate(answers, start=1):
            answer += f"{answ_id}. {answr}\n"
        answer += f"Верный ответ: {correct_answer}.\n"
        builder.add(
            InlineKeyboardButton(
                text=f"{idx}",
                callback_data=f"EditQuestion_{id}_Quiz_{quiz_id}"))
    builder.adjust(3, 8, 8)
    await callback.message.answer("Выберите редактируемый вопрос: \n" + answer,
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("EditQuestion_"))
async def edit_question_in_quiz(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    _, question_id, _, quiz_id = callback.data.split("_")
    builder.add(
        InlineKeyboardButton(text="Вернуться к квизу",
                             callback_data=f"EditQuizAdmin_{quiz_id}"))
    builder.add(
        InlineKeyboardButton(
            text="Редактировать вопрос",
            callback_data=f"EditQuestionQuestion_{question_id}_{quiz_id}",
        ))
    for idx in range(1, 5):
        builder.add(
            InlineKeyboardButton(
                text=f"Редактировать {idx} ответ",
                callback_data=
                f"EditAnswerQuestion_{question_id}_{quiz_id}_{idx}",
            ))
    builder.add(
        InlineKeyboardButton(
            text="Редактировать верный ответ",
            callback_data=f"EditCorrectAnswerQuestion_{question_id}_{quiz_id}",
        ))
    builder.add(
        InlineKeyboardButton(
            text="Удалить вопрос",
            callback_data=f"DeleteQuizQuestion_{question_id}"))
    builder.adjust(1)
    data = database.get_question_by_id(question_id)
    question, *answers, correct_answer = data
    answer_to = f"Вопрос: {question}\n Ответы:\n"
    for idx, answer in enumerate(answers, start=1):
        answer_to += f"{idx}. {answer}\n"
    answer_to += f"Верный ответ: {correct_answer}"
    await callback.message.answer(answer_to, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("EditQuestionQuestion"))
async def edit_question_question_in_quiz(callback: CallbackQuery,
                                         state: FSMContext):
    _, question_id, quiz_id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data=f"EditQuestion_{question_id}_Quiz_{quiz_id}",
        ))
    await state.set_state(AdminStates.edit_question_question)
    await state.set_data({"question_id": question_id, "quiz_id": quiz_id})
    await callback.message.answer("Введите новый текст вопроса",
                                  reply_markup=builder.as_markup())


@router.message(AdminStates.edit_question_question)
async def edit_question_question_in_quiz_enter(message: Message,
                                               state: FSMContext):
    question_text = message.text
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data="EditQuestion_{}_Quiz_{}".format(
                data["question_id"], data["quiz_id"]),
        ))
    database.set_question_parameter_value_by_id("question", question_text,
                                                data["question_id"])
    await message.answer(f"Текст вопроса успешно изменен на {question_text}")


@router.callback_query(F.data.startswith("EditAnswerQuestion"))
async def edit_answer_question_in_quiz(callback: CallbackQuery,
                                       state: FSMContext):
    _, question_id, quiz_id, answer_num = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data=f"EditQuestion_{question_id}_Quiz_{quiz_id}",
        ))
    await state.set_state(AdminStates.edit_answer_question)
    await state.set_data({
        "question_id": question_id,
        "quiz_id": quiz_id,
        "answer_num": answer_num
    })
    await callback.message.answer("Введите новый текст ответа",
                                  reply_markup=builder.as_markup())


@router.message(AdminStates.edit_answer_question)
async def edit_answer_question_in_quiz_enter(message: Message,
                                             state: FSMContext):
    answer_text = message.text
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data="EditQuestion_{}_Quiz_{}".format(
                data["question_id"], data["quiz_id"]),
        ))
    match int(data["answer_num"]):
        case 1:
            database.set_question_parameter_value_by_id(
                "first_answer", answer_text, data["question_id"])
        case 2:
            database.set_question_parameter_value_by_id(
                "second_answer", answer_text, data["question_id"])
        case 3:
            database.set_question_parameter_value_by_id(
                "third_answer", answer_text, data["question_id"])
        case 4:
            database.set_question_parameter_value_by_id(
                "fourth_answer", answer_text, data["question_id"])
    await message.answer(f"Текст ответа успешно изменен на {answer_text}")


@router.callback_query(F.data.startswith("EditCorrectAnswerQuestion"))
async def edit_correct_answer_question_in_quiz(callback: CallbackQuery,
                                               state: FSMContext):
    _, question_id, quiz_id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data=f"EditQuestion_{question_id}_Quiz_{quiz_id}",
        ))
    await state.set_state(AdminStates.edit_correct_answer_question)
    await state.set_data({"question_id": question_id, "quiz_id": quiz_id})
    await callback.message.answer("Введите новый номер верного ответа",
                                  reply_markup=builder.as_markup())


@router.message(AdminStates.edit_correct_answer_question)
async def edit_correct_answer_question_in_quiz_enter(message: Message,
                                                     state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Вернуться к вопросу",
            callback_data="EditQuestion_{}_Quiz_{}".format(
                data["question_id"], data["quiz_id"]),
        ))
    search = re.search(r"\d+", message.text)
    if not search:
        await message.answer(text="Нужно ввести число",
                             reply_markup=builder.as_markup())
        await state.clear()
        return
    correct_answer = int(search.group())
    if correct_answer > 4 or correct_answer < 1:
        await message.answer(
            text="Число должно быть от 1 до 4, включительно",
            reply_markup=builder.as_markup(),
        )
        return
    database.set_question_parameter_value_by_id("correct_answer",
                                                correct_answer,
                                                data["question_id"])
    await message.answer(
        f"Новый номер верного ответа изменён на {correct_answer}")


@router.callback_query(F.data.startswith("AddQuestion_Quiz_"))
async def add_question_in_quiz(callback: CallbackQuery, state: FSMContext):
    _, _, quiz_id = callback.data.split("_")
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в квизы",
                             callback_data="EditQuizzesAdmin"))
    await state.set_data({"quiz_id": quiz_id})
    await state.set_state(AdminStates.add_question_quiz)
    await callback.message.answer(
        """
Введите вопрос в таком формате:
[Текст вопроса][Первый вариант ответа][Второй вариант ответа][Третий вариант ответа][Четвёртый вариант ответа][Номер верного ответа]
Пример: [Когда Наполеон начал войну][1582г.][1917г.][1812г.][1783г.][3]
Если передумали добавлять вопрос, вернитесь в квизы""",
        reply_markup=builder.as_markup(),
    )


@router.message(AdminStates.add_question_quiz)
async def add_question_quiz_confirm(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Вернуться в квизы",
                             callback_data="EditQuizzesAdmin"))
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
        await state.set_state(AdminStates.add_question_quiz)
        return
    if not data["quiz_id"]:
        await message.answer(
            "Вернитесь в квиз и нажмите добавить вопрос снова.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()
        return
    count = database.get_quiestions_len_by_quiz_id(data["quiz_id"])
    if count > 19:
        await message.answer(
            "Этот квиз имеет максимальное количество вопросов",
            reply_markup=builder.as_markup(),
        )
        return
    text = list(
        map(lambda x: x.replace("[", "").replace("]", ""),
            message.text.split("][")))
    (
        question_text,
        first_answer,
        second_answer,
        third_answer,
        fourth_answer,
        correct_answer,
    ) = text
    database.create_question(
        question_text,
        first_answer,
        second_answer,
        third_answer,
        fourth_answer,
        correct_answer,
        data["quiz_id"],
    )
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
    # await state.set_state(AdminStates.add_question_quiz)


@router.callback_query(F.data.startswith("DeleteQuizQuestion_"))
async def delete_quiz_question_admin(callback: CallbackQuery,
                                     state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Вернуться к квизам",
                             callback_data="EditQuizzesAdmin"))
    question_id = callback.data.split("_")[1]
    database.delete_question_by_id(question_id)
    await callback.message.answer("Вопрос успешно удалён!",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("DeleteQuiz_"))
async def delete_quiz_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Вернуться к квизам",
                             callback_data="EditQuizzesAdmin"))
    quiz_id = callback.data.split("_")[1]
    database.delete_quiz_by_id(quiz_id)
    await callback.message.answer("Квиз успешно удалён!",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data == "AddQuizAdmin")
async def add_quiz_admin(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="В список квизов",
                             callback_data="EditQuizzesAdmin"))
    count = database.get_quizzes_len()
    if count > 20:
        callback.message.answer(
            "Максимальное количество квизов, больше добавить нельзя",
            reply_markup=builder.as_markup(),
        )
    await callback.message.answer(
        """
Введите квиз полностью в одном сообщении в формате:
[Название][Описание][Награда]
Пример: [Квиз на то, получишь ли ты бабки][Здесь что-то про квиз, ну понятно][3 Lucky](Может быть Lucky, Cash Online или E Coin, при награде в монетах ОБЯЗАТЕЛЬНО писать валюту!)
Наградой возможен мерч, если мерч, вписывать цифры его id, например [5] (Смотреть в просмотре мерча через панель админа)""",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(AdminStates.add_quiz)


@router.message(AdminStates.add_quiz)
async def add_quiz_admin_enter(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="В список квизов",
                             callback_data="EditQuizzesAdmin"))
    if message.text.count("[") != 3 or message.text.count("]") != 3:
        await message.answer(
            """
Введите квиз в таком формате:
[Название][Описание][Награда]
Пример: [Квиз на то, получишь ли ты бабки][Здесь что-то про квиз, ну понятно][3 Lucky](Может быть Lucky, Cash Online или E Coin, при награде в монетах ОБЯЗАТЕЛЬНО писать валюту!)
Наградой возможен мерч, если мерч, вписывать цифры его id, например [5] (Смотреть в просмотре мерча через панель админа)""",
            reply_markup=builder.as_markup(),
        )
        await state.set_state(AdminStates.add_question_quiz)
        return
    text = list(
        map(lambda x: x.replace("[", "").replace("]", ""),
            message.text.split("][")))
    name, description, reward = text
    database.create_quiz(name, description, reward)
    await message.answer(
        f"""
Квиз принят!
Ваш квиз: [{name}][{description}][{reward}]
Теперь добавьте вопросы.
Для этого вернитесь в список квизов и добавьте вопросы через кнопку.""",
        reply_markup=builder.as_markup(),
    )
    await state.clear()
