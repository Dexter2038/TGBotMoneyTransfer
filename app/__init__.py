from aiogram import Bot, Dispatcher
from aiogram.utils.token import TokenValidationError
from aiogram.client.default import DefaultBotProperties
from typing import Tuple
from dotenv import load_dotenv
from loguru import logger
from os import environ
from app.handlers import get_router
import asyncio
from app.utils import database
import app.states

load_dotenv()
database.init()


def get_bot_and_dispatcher() -> Tuple[Bot, Dispatcher]:
    try:
        bot = Bot(token=environ["TELEGRAM-TOKEN"],
                  default=DefaultBotProperties(parse_mode="HTML",
                                               protect_content=True))
    except TokenValidationError as e:
        logger.error(e)
        exit(1)
    except KeyError as e:
        logger.error("Токен телеграм бота не задан")
        exit(1)
    dp = Dispatcher(bot=bot)
    dp.include_router(get_router())
    return bot, dp
