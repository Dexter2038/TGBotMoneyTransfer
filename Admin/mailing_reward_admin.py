from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import AdminStates

router = Router()


@router.callback_query(F.data == "SetChannelReward")
async def set_channel_reward(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Введите награду за подписку на канал.\nЕсли награда - мерч, напишите id мерча, например - 5\n Если награда в монетах - напишите в формате: сумма валюта, например - 5 Lucky, или 8 Cash Online"
    )
    await state.set_state(AdminStates.set_sub_reward)


@router.message(AdminStates.set_sub_reward)
async def set_channel_reward_enter(message: Message, state: FSMContext):
    if not message.text.isdigit():
        reward_sum = message.text.split(" ")[0]
        reward_currency = message.text.replace(f"{reward_sum} ", "")
        if len(reward_currency.split("_")) > 2:
            return
        sub_reward = f"{reward_sum} {reward_currency.capitalize()}"
    else:
        sub_reward = message.text
    await message.answer(f"Награда за реферала изменена на: {sub_reward}")


@router.callback_query(F.data == "SetRefReward")
async def set_ref_reward(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Админ панель", callback_data="Admin"))
    await callback.message.answer(
        "Введите награду за реферала.\nЕсли награда - мерч, напишите id мерча, например - 5\n Если награда в монетах - напишите в формате: сумма валюта, например - 5 Lucky, или 8 Cash Online"
    )
    await state.set_state(AdminStates.set_ref_reward)


@router.message(AdminStates.set_ref_reward)
async def set_ref_reward_enter(message: Message, state: FSMContext):
    if not message.text.isdigit():
        reward_sum = message.text.split(" ")[0]
        reward_currency = message.text.replace(f"{reward_sum} ", "")
        if len(reward_currency.split("_")) > 2:
            return
        ref_reward = f"{reward_sum} {reward_currency.capitalize()}"
    else:
        ref_reward = message.text
    await message.answer(f"Награда за реферала изменена на: {ref_reward}")
