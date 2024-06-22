from app import get_bot_and_dispatcher
import asyncio

if __name__ == "__main__":
    bot, dp = get_bot_and_dispatcher()
    asyncio.get_event_loop().run_until_complete(dp.start_polling(bot))
