from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils import database
import cv2
import json

router = Router()


@router.message(F.photo)
async def scan_qr(message: Message, state: FSMContext, bot: Bot):
    if not database.get_admin_by_chat_id(message.chat.id):
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
            status = database.get_withdraw_status_by_amount_and_id(
                data["qr_id"])
            if status == 1:
                await message.answer("""
QRCode уже был активирован.
Чтобы вывести деньги снова, нужно получить новый QRCode.""")
                return
            elif status is None:
                await message.answer("""
Такого QRCode`а не существует.
Возможна махинация.""")
                return
            status = database.get_withdraw_status_by_amount_and_id(
                data["qr_id"], data["amount"])
            if status is None:
                await message.answer("""
Сумма QRCode`а зарегистрированного по этому id не совпадает с текущим QRCode`ом.
Возможна махинация.""")
                return
            datum = database.get_cash_online_user_name_username_by_user_id(
                data["user_id"])
            available, first_name, last_name, username = datum
            if available < data["amount"]:
                await message.answer("""
У клиента %s %s с никнеймом @%s недостаточно Cash Online.
У клиента на балансе %s Cash Online.
Клиент собирается вывести %s Cash Online.""" %
                                     (last_name, first_name, username,
                                      available, data["amount"]))
                return
            database.set_withdraw_qr_status_by_id(data["qr_id"])
            database.create_transaction_default(2, data["user_id"],
                                                data["amount"], 1)
            await message.answer("""
Клиент: %s %s, никнейм @%s.
Сумма: %s Cash Online.""" % (last_name, first_name, username, data["amount"]))
        case "transactions":
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(
                    text="Просмотреть историю транзакций",
                    callback_data="SeeTransactionsQR_0_{}".format(
                        data["user_id"]),
                ))
            await message.answer("Просмотреть историю транзакций?",
                                 reply_markup=builder.as_markup())
