from aiogram import Bot
from aiogram.types import User as TgUser, InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import settings

MEAL_LABELS = {
    "all_inclusive": "Всё включено 🍽",
    "breakfast": "Завтраки 🥐",
    "no_meal": "Без питания",
    "any": "Без разницы",
}

DATE_LABELS = {
    "2weeks": "В ближайшие 2 недели",
    "1month": "Через месяц",
    "2-3months": "Через 2–3 месяца",
    "3months+": "Более чем через 3 месяца",
    "flexible": "Гибкая дата",
}


async def notify_manager_new_request(bot: Bot, data: dict, user: TgUser):
    """Отправляет менеджеру карточку с новой заявкой из бота"""
    if not settings.MANAGER_CHAT_ID:
        return

    children_info = ""
    if data.get("children", 0) > 0:
        ages = data.get("children_ages", "не указан")
        children_info = f"👶 Детей: {data['children']} (возраст: {ages})\n"

    username_str = f"@{user.username}" if user.username else "нет username"

    text = (
        f"🆕 *Новая заявка из бота!*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 Клиент: {user.full_name}\n"
        f"📱 TG: {username_str} | `{user.id}`\n"
        f"📞 Телефон: {data.get('phone', '—')}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🌍 Направление: *{data.get('destination', '—')}*\n"
        f"📅 Вылет: {DATE_LABELS.get(data.get('departure_date'), data.get('departure_date', '—'))}\n"
        f"👥 Взрослых: {data.get('adults', 2)}\n"
        f"{children_info}"
        f"🌙 Ночей: {data.get('nights', '—')}\n"
        f"💰 Бюджет: {data.get('budget', '—')} на чел.\n"
        f"🍽 Питание: {MEAL_LABELS.get(data.get('meal'), '—')}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="💬 Написать клиенту",
            url=f"tg://user?id={user.id}"
        )
    ]])

    await bot.send_message(
        settings.MANAGER_CHAT_ID,
        text,
        parse_mode="Markdown",
        reply_markup=kb
    )


async def notify_manager_tourvisor_order(bot: Bot, order_data: dict):
    """Уведомление о новой заявке с сайта через Tourvisor webhook"""
    if not settings.MANAGER_CHAT_ID:
        return

    text = (
        f"🌐 *Заявка с сайта (Tourvisor)*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 Клиент: {order_data.get('name', '—')}\n"
        f"📞 Телефон: {order_data.get('phone', '—')}\n"
        f"📧 Email: {order_data.get('email', '—')}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🌍 Страна: *{order_data.get('country', '—')}*\n"
        f"🏨 Отель: {order_data.get('hotel', '—')}\n"
        f"✈️ Вылет: {order_data.get('flydate', '—')} из {order_data.get('departure', '—')}\n"
        f"🌙 Ночей: {order_data.get('nights', '—')}\n"
        f"👥 Размещение: {order_data.get('placement', '—')}\n"
        f"🍽 Питание: {order_data.get('meal', '—')}\n"
        f"💰 Стоимость: {order_data.get('price', '—')} {order_data.get('currency', '')}\n"
        f"🏢 Оператор: {order_data.get('operator', '—')}\n"
    )

    if order_data.get("comments"):
        text += f"💬 Комментарий: {order_data['comments']}\n"

    await bot.send_message(
        settings.MANAGER_CHAT_ID,
        text,
        parse_mode="Markdown"
    )
