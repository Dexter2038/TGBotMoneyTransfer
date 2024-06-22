from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils import database
from app.states import AdminStates

router = Router(name="admin-start-mailing")


@router.callback_query(F.data == "StartMailing")
async def start_mailing(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(text="Реферальная ссылка",
                             callback_data="MailingRef"))
    builder.row(
        InlineKeyboardButton(text="Подписка на канал",
                             callback_data="MailingLink"))
    builder.row(
        InlineKeyboardButton(text="Выставить награду за реферала",
                             callback_data="SetRefReward"))
    builder.row(
        InlineKeyboardButton(
            text="Выставить награду за подписку на канал",
            callback_data="SetChannelReward",
        ))
    await callback.message.answer("Выберите способ рассылки",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data == "MailingRef")
async def start_ref_mailing(callback: CallbackQuery, state: FSMContext,
                            bot: Bot):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    chat_ids = database.get_chat_ids()
    for chat_id in chat_ids:
        await bot.send_message(
            int(chat_id[0]),
            f"Пригласите друга по своей ссылке и получите подарок, войдя в 'Подарки' и нажав на 'Забрать подарок за реферала'.\nНайти свою ссылку можно по команде /ref",
        )


@router.callback_query(F.data == "MailingLink")
async def start_link_mailing(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        text="Введите ссылку, по которой нужно войти",
        reply_markup=builder.as_markup())
    await state.set_state(AdminStates.mailing_link)


@router.message(AdminStates.mailing_link)
async def enter_link_mailing(message: Message, state: FSMContext):
    link = message.text.split(" ")[0]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    builder.row(
        InlineKeyboardButton(text="Подтвердить",
                             callback_data=f"MailingLinkConfirm_"))
    await state.set_data({"link": link})
    await message.answer(
        text=f"Ваша ссылка: {link}. Вы хотите отправить её в рассылку?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("MailingLinkConfirm_"))
async def confirm_link_mailing(callback: CallbackQuery, state: FSMContext,
                               bot: Bot):
    link = (await state.get_data())["link"]
    cur_link = link
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    chat_ids = database.get_chat_ids()
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Подписаться", url=link))
    database.set_no_subscription_to_all()
    for chat_id in chat_ids:
        await bot.send_message(
            int(chat_id[0]),
            f"Подпишитесь на канал, войдите в подарки, нажмите 'Я подписался' и получите подарок!",
            reply_markup=keyboard.as_markup(),
        )
