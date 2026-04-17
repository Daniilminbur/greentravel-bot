"""
Запусти этот скрипт ОДИН РАЗ чтобы зарегистрировать команды в BotFather.
После этого они появятся в меню "/" у всех пользователей.

Запуск:
    python set_commands.py
"""

import asyncio
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from bot.config import settings


USER_COMMANDS = [
    BotCommand(command="start",       description="🏠 Главное меню"),
    BotCommand(command="tour",        description="✈️ Подобрать тур"),
    BotCommand(command="hot",         description="🔥 Горящие туры"),
    BotCommand(command="subscribe",   description="🔔 Подписка на горящие туры"),
    BotCommand(command="unsubscribe", description="🔕 Отписаться от горящих туров"),
    BotCommand(command="contacts",    description="📞 Контакты агентства"),
    BotCommand(command="reviews",     description="⭐ Отзывы клиентов"),
    BotCommand(command="help",        description="ℹ️ Помощь и список команд"),
    BotCommand(command="cancel",      description="❌ Отменить текущее действие"),
]

# Команды только для администраторов
ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand(command="requests",    description="📋 Новые заявки"),
    BotCommand(command="stats",       description="📊 Статистика"),
    BotCommand(command="broadcast",   description="📢 Рассылка по базе"),
    BotCommand(command="addreview",   description="⭐ Добавить отзыв"),
]


async def set_commands():
    bot = Bot(token=settings.BOT_TOKEN)

    # Команды для всех пользователей
    await bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeDefault())
    print("✅ Команды для пользователей установлены")

    # Расширенные команды для каждого администратора
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                ADMIN_COMMANDS,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
            print(f"✅ Админ-команды установлены для {admin_id}")
        except Exception as e:
            print(f"⚠️ Не удалось установить команды для {admin_id}: {e}")

    # Описание бота (показывается в профиле)
    await bot.set_my_description(
        "🌴 Бот турагентства Green Travel\n\n"
        "Подберём тур мечты, пришлём горящие предложения и ответим на все вопросы!"
    )

    # Краткое описание (показывается до старта)
    await bot.set_my_short_description("✈️ Подбор туров и горящие предложения от Green Travel")

    print("\n🎉 Всё готово! Команды появятся в боте через несколько секунд.")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(set_commands())
