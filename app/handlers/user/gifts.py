from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import ref_reward, cur_link, sub_reward
from app.utils import database
import re

router = Router(name="user-gifts")


@router.callback_query(F.data == "Gifts")
async def gifts(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    builder.add(InlineKeyboardButton(text="Квизы", callback_data="Quizzes"))
    builder.add(
        InlineKeyboardButton(text="Забрать подарок за реферала",
                             callback_data="RefReward"))
    builder.add(
        InlineKeyboardButton(text="Забрать подарок за подписку",
                             callback_data="SubscriptionReward"))
    builder.adjust(2)
    await callback.message.answer("Выберите опцию:",
                                  reply_markup=builder.as_markup())


@router.callback_query(F.data == "RefReward")
async def get_ref_reward(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    user_id, referal = database.get_user_id_invited_status_by_chat_id(
        callback.message.chat.id)
    if not referal:
        await callback.message.answer("У вас отсутствуют рефералы",
                                      reply_markup=builder.as_markup())
        return
    if ref_reward.is_digit():
        data = database.get_merch_id_name_cost_by_merch_id(ref_reward)
        merch_id, name, cost = data
        database.create_order(merch_id, 0, user_id)
        await callback.message.answer(
            f"Вы выиграли мерч! {name} за {cost} БЕСПЛАТНО!")
    else:
        value = ref_reward.split(" ")[0]
        reward_currency = ref_reward.replace(f"{value} ", "")
        bd_reward_currency = reward_currency.replace(" ", "_").lower()
        database.set_money_by_chat_id("+", bd_reward_currency, value,
                                      callback.message.chat.id)
        await callback.message.answer(f"Вы выиграли {value} {reward_currency}!"
                                      )
    database.set_money_by_chat_id("-", "invite", 1, callback.message.chat.id)


@router.callback_query(F.data == "SubscriptionReward")
async def get_subscription_reward(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Профиль", callback_data="Profile"))
    user_id, subscription = database.get_user_id_subscribed_status_by_chat_id(
        callback.message.chat.id)
    if not cur_link:
        await callback.message.answer(
            "Награда за подписку на канал пока что недоступна")
        return
    if subscription:
        await callback.message.answer("Вы уже забрали награду за подписку")
        return
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(KeyboardButton(text="Я подписан"))
    await callback.message.answer("Вы подписаны?", reply_markup=keyboard)


@router.message(F.text.lower() == "я подписан")
async def check_subscription(message: Message, state: FSMContext, bot: Bot):
    link = cur_link
    user_id = message.from_user.id
    user_channel_status = await bot.get_chat_member(chat_id=f"@{link[13:]}",
                                                    user_id=user_id)
    user_channel_status = re.findall(r"\w*", str(user_channel_status))
    if database.get_subscribed_status_by_chat_id(message.chat.id):
        await message.answer("Вы уже забрали награду за подписку")
        return
    try:
        if user_channel_status[70] != "left":
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="Профиль", callback_data="Profile"))
            user_id = database.get_user_id_by_chat_id(message.chat.id)
            if sub_reward.is_digit():
                data = database.get_merch_id_name_cost_by_merch_id(sub_reward)
                merch_id, name, cost = data
                database.create_order(merch_id, 0, user_id)
                await message.answer(
                    f"Вы выиграли мерч! {name} за {cost} БЕСПЛАТНО!")
            else:
                value = sub_reward.split(" ")[0]
                reward_currency = sub_reward.replace(f"{value} ", "")
                bd_reward_currency = reward_currency.replace(" ", "_").lower()
                database.set_money_by_chat_id("+", bd_reward_currency, value,
                                              message.chat.id)
                await message.answer(f"Вы выиграли {value} {reward_currency}!")
        else:
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="Подписаться", url=cur_link[19:]))
            await message.answer("Вы не подписаны",
                                 reply_markup=builder.as_markup())
            return
    except:
        if user_channel_status[60] != "left":
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="Профиль", callback_data="Profile"))
            user_id = database.get_user_id_by_chat_id(message.chat.id)
            if sub_reward.is_digit():
                data = database.get_merch_id_name_cost_by_merch_id(sub_reward)
                merch_id, name, cost = data
                database.create_order(merch_id, 0, user_id)
                await message.answer(
                    f"Вы выиграли мерч! {name} за {cost} БЕСПЛАТНО!")
            else:
                value = sub_reward.split(" ")[0]
                reward_currency = sub_reward.replace(f"{value} ", "")
                bd_reward_currency = reward_currency.replace(" ", "_").lower()
                database.set_money_by_chat_id("+", bd_reward_currency, value,
                                              message.chat.id)
                await message.answer(f"Вы выиграли {value} {reward_currency}!")
        else:
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="Подписаться", url=cur_link[19:]))
            await message.answer("Вы не подписаны",
                                 reply_markup=builder.as_markup())
            return
    database.set_yes_sunscription_to_chat_id(message.chat.id)
