import asyncio
import logging
import os
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.database.crud import init_db
from bot.handlers import start, tour_search, hot_tours, reviews, favorites, history
from webhook.server import set_bot, poll_tourvisor_orders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from admin.app import app as admin_app


async def polling_loop(bot: Bot):
    last_id = 0
    while True:
        await asyncio.sleep(300)
        last_id = await poll_tourvisor_orders(bot, last_id)


async def run_bot():
    from test_api import test_tourvisor_api
    await test_tourvisor_api()
    await init_db()
    logger.info("✅ БД инициализирована")

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(tour_search.router)
    dp.include_router(hot_tours.router)
    dp.include_router(reviews.router)
    dp.include_router(favorites.router)
    dp.include_router(history.router)

    set_bot(bot)
    asyncio.create_task(polling_loop(bot))

    logger.info("🚀 Бот запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main():
    port = int(os.environ.get("PORT", 8080))
    bot_task = asyncio.create_task(run_bot())

    config = uvicorn.Config(admin_app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    logger.info(f"✅ Админ-панель запущена на порту {port}")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
