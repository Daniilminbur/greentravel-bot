from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔍 Подобрать тур"),
        KeyboardButton(text="🔥 Горящие туры"),
    )
    builder.row(
        KeyboardButton(text="📬 Подписка на горящие"),
        KeyboardButton(text="❤️ Избранное"),
    )
    builder.row(
        KeyboardButton(text="🕐 История поиска"),
        KeyboardButton(text="⭐ Отзывы"),
    )
    builder.row(
        KeyboardButton(text="📢 Наш канал"),
        KeyboardButton(text="💬 Связь с менеджером"),
    )
    builder.row(
        KeyboardButton(text="🤖 Подобрать с ИИ"),
        KeyboardButton(text="📞 Контакты"),
    )
    return builder.as_markup(resize_keyboard=True)


# ── Тип отдыха ───────────────────────────────────────────────────────────────

def rest_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏖 Море и пляж", callback_data="rest:sea")
    builder.button(text="🏛 Экскурсии и культура", callback_data="rest:excursions")
    builder.button(text="⛰ Горы и природа", callback_data="rest:mountains")
    builder.button(text="🤷 Без разницы", callback_data="rest:any")
    builder.adjust(2)
    return builder.as_markup()


# ── Направления ──────────────────────────────────────────────────────────────

POPULAR_DESTINATIONS = [
    ("🇹🇷 Турция", "Турция"),
    ("🇪🇬 Египет", "Египет"),
    ("🇦🇪 ОАЭ", "ОАЭ"),
    ("🇹🇭 Таиланд", "Таиланд"),
    ("🇲🇻 Мальдивы", "Мальдивы"),
    ("🇬🇷 Греция", "Греция"),
    ("🇪🇸 Испания", "Испания"),
    ("🇮🇩 Бали", "Бали"),
    ("✏️ Другое", "other"),
]

def destinations_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, data in POPULAR_DESTINATIONS:
        builder.button(text=label, callback_data=f"dest:{data}")
    builder.adjust(2)
    return builder.as_markup()


# ── Дата вылета ──────────────────────────────────────────────────────────────

DEPARTURE_OPTIONS = [
    ("📅 В ближайшие 2 недели", "2weeks"),
    ("📅 Через месяц", "1month"),
    ("📅 Через 2–3 месяца", "2-3months"),
    ("📅 Более чем через 3 месяца", "3months+"),
    ("📅 Дата гибкая", "flexible"),
]

def departure_date_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, data in DEPARTURE_OPTIONS:
        builder.button(text=label, callback_data=f"date:{data}")
    builder.adjust(1)
    return builder.as_markup()


# ── Взрослые ─────────────────────────────────────────────────────────────────

def adults_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 7):
        builder.button(text=str(i), callback_data=f"adults:{i}")
    builder.adjust(3)
    return builder.as_markup()


# ── Дети ─────────────────────────────────────────────────────────────────────

def children_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👶 Нет детей", callback_data="children:0")
    for i in range(1, 5):
        builder.button(text=f"{i} реб.", callback_data=f"children:{i}")
    builder.adjust(2)
    return builder.as_markup()


# ── Ночей ─────────────────────────────────────────────────────────────────────

NIGHTS_OPTIONS = [
    ("5–7 ночей", "5-7"),
    ("7–10 ночей", "7-10"),
    ("10–14 ночей", "10-14"),
    ("14+ ночей", "14+"),
]

def nights_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, data in NIGHTS_OPTIONS:
        builder.button(text=label, callback_data=f"nights:{data}")
    builder.adjust(2)
    return builder.as_markup()


# ── Бюджет ────────────────────────────────────────────────────────────────────

BUDGET_OPTIONS = [
    ("до $500", "500"),
    ("$500–$800", "800"),
    ("$800–$1200", "1200"),
    ("$1200–$2000", "2000"),
    ("$2000+", "2000+"),
    ("Бюджет гибкий", "flexible"),
]

def budget_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, data in BUDGET_OPTIONS:
        builder.button(text=label, callback_data=f"budget:{data}")
    builder.adjust(2)
    return builder.as_markup()


# ── Питание ───────────────────────────────────────────────────────────────────

MEAL_OPTIONS = [
    ("🍽 Всё включено", "all_inclusive"),
    ("🥐 Завтраки", "breakfast"),
    ("🏨 Без питания", "no_meal"),
    ("🤷 Без разницы", "any"),
]

def meal_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, data in MEAL_OPTIONS:
        builder.button(text=label, callback_data=f"meal:{data}")
    builder.adjust(2)
    return builder.as_markup()


# ── Подтверждение ─────────────────────────────────────────────────────────────

def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить заявку", callback_data="request:confirm")
    builder.button(text="🔄 Начать заново", callback_data="request:restart")
    builder.adjust(1)
    return builder.as_markup()


# ── Подписка ──────────────────────────────────────────────────────────────────

def subscription_destinations_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    destinations = [
        ("🇹🇷 Турция", "Турция"), ("🇪🇬 Египет", "Египет"),
        ("🇦🇪 ОАЭ", "ОАЭ"), ("🇹🇭 Таиланд", "Таиланд"),
        ("🇬🇷 Греция", "Греция"), ("🇲🇻 Мальдивы", "Мальдивы"),
        ("🌍 Любое направление", "any"),
    ]
    for label, data in destinations:
        builder.button(text=label, callback_data=f"sub_dest:{data}")
    builder.adjust(2)
    return builder.as_markup()


# ── Кнопки под постом канала ─────────────────────────────────────────────────

def channel_post_kb(destination: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    dest_param = f"_{destination}" if destination else ""
    builder.button(
        text="✈️ Хочу такой тур",
        url=f"https://t.me/GreentravelbelarusBot?start=tour{dest_param}"
    )
    if destination:
        builder.button(
            text="🔔 Подписаться на похожие",
            url=f"https://t.me/GreentravelbelarusBot?start=sub_{destination}"
        )
    builder.adjust(1)
    return builder.as_markup()
