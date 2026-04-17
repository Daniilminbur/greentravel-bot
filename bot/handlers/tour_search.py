from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main_menu import (
    destinations_kb, departure_date_kb, adults_kb,
    children_kb, nights_kb, budget_kb, meal_kb, confirm_kb, rest_type_kb
)
from bot.database.crud import create_tour_request, async_session, save_search_history, get_search_history, update_user_preferences, get_user

router = Router()


class TourWizard(StatesGroup):
    rest_type = State()       # тип отдыха
    destination = State()
    destination_custom = State()
    departure_date = State()
    adults = State()
    children = State()
    children_ages = State()
    nights = State()
    budget = State()
    meal = State()
    phone = State()
    confirm = State()


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

REST_LABELS = {
    "sea": "🏖 Море и пляж",
    "excursions": "🏛 Экскурсии и культура",
    "mountains": "⛰ Горы и природа",
    "any": "🤷 Без разницы",
}


def build_summary(data: dict) -> str:
    return (
        f"📋 *Ваша заявка:*\n\n"
        f"🌴 Тип отдыха: {REST_LABELS.get(data.get('rest_type', 'any'), '—')}\n"
        f"🌍 Направление: *{data.get('destination', '—')}*\n"
        f"📅 Вылет: {DATE_LABELS.get(data.get('departure_date'), data.get('departure_date', '—'))}\n"
        f"👥 Взрослых: {data.get('adults', '—')}\n"
        f"👶 Детей: {data.get('children', 0)}"
        + (f" (возраст: {data.get('children_ages')})" if data.get('children_ages') else "") + "\n"
        f"🌙 Ночей: {data.get('nights', '—')}\n"
        f"💰 Бюджет: {data.get('budget', '—')} на чел.\n"
        f"🍽 Питание: {MEAL_LABELS.get(data.get('meal'), data.get('meal', '—'))}\n"
        f"📱 Телефон: {data.get('phone', '—')}\n"
    )


@router.message(F.text == "🔍 Подобрать тур")
async def start_wizard(message: Message, state: FSMContext):
    await state.clear()

    # Проверяем есть ли история поиска
    async with async_session() as session:
        history = await get_search_history(session, message.from_user.id)
        user = await get_user(session, message.from_user.id)

    if history:
        last = history[0]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🔄 Повторить: {last.destination or '—'}, {last.budget or '—'}", callback_data="wizard:repeat")],
            [InlineKeyboardButton(text="✨ Новый поиск", callback_data="wizard:new")]
        ])
        await message.answer(
            "✈️ *Подбор тура*\n\nХотите повторить последний поиск или начать новый?",
            parse_mode="Markdown",
            reply_markup=kb
        )
    else:
        await state.set_state(TourWizard.rest_type)
        await message.answer(
            "✈️ *Подбор тура за 1 минуту!*\n\nКакой отдых вас интересует?",
            parse_mode="Markdown",
            reply_markup=rest_type_kb()
        )


@router.callback_query(F.data == "wizard:new")
async def wizard_new(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TourWizard.rest_type)
    await callback.message.edit_text(
        "✈️ *Подбор тура за 1 минуту!*\n\nКакой отдых вас интересует?",
        parse_mode="Markdown",
        reply_markup=rest_type_kb()
    )


@router.callback_query(F.data == "wizard:repeat")
async def wizard_repeat(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        history = await get_search_history(session, callback.from_user.id)

    if not history:
        await wizard_new(callback, state)
        return

    last = history[0]
    data = {
        "rest_type": "any",
        "destination": last.destination,
        "departure_date": last.departure_date,
        "adults": last.adults,
        "children": last.children,
        "nights": last.nights,
        "budget": last.budget,
        "meal": last.meal,
    }
    await state.update_data(**data)
    await state.set_state(TourWizard.phone)
    await callback.message.edit_text(
        f"🔄 *Повторяем поиск:*\n\n"
        f"🌍 {last.destination or '—'} | 💰 {last.budget or '—'} | 🌙 {last.nights or '—'} ночей\n\n"
        f"📱 Укажите ваш телефон для связи:",
        parse_mode="Markdown"
    )


# ── Тип отдыха ───────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.rest_type, F.data.startswith("rest:"))
async def set_rest_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(rest_type=value)
    await state.set_state(TourWizard.destination)
    await callback.message.edit_text(
        f"✅ {REST_LABELS.get(value, value)}\n\n🌍 Куда хотите поехать?",
        reply_markup=destinations_kb()
    )


# ── Направление ──────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.destination, F.data.startswith("dest:"))
async def set_destination(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]

    if value == "other":
        await state.set_state(TourWizard.destination_custom)
        await callback.message.edit_text("✏️ Напишите направление (страну или курорт):")
        return

    await state.update_data(destination=value)
    await state.set_state(TourWizard.departure_date)
    await callback.message.edit_text(
        f"✅ *{value}*\n\n📅 Когда планируете вылет?",
        parse_mode="Markdown",
        reply_markup=departure_date_kb()
    )


@router.message(TourWizard.destination_custom)
async def set_destination_custom(message: Message, state: FSMContext):
    await state.update_data(destination=message.text)
    await state.set_state(TourWizard.departure_date)
    await message.answer(
        f"✅ *{message.text}*\n\n📅 Когда планируете вылет?",
        parse_mode="Markdown",
        reply_markup=departure_date_kb()
    )


# ── Дата ─────────────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.departure_date, F.data.startswith("date:"))
async def set_date(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(departure_date=value)
    await state.set_state(TourWizard.adults)
    await callback.message.edit_text("👥 Сколько взрослых?", reply_markup=adults_kb())


# ── Взрослые ─────────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.adults, F.data.startswith("adults:"))
async def set_adults(callback: CallbackQuery, state: FSMContext):
    value = int(callback.data.split(":")[1])
    await state.update_data(adults=value)
    await state.set_state(TourWizard.children)
    await callback.message.edit_text("👶 Едут ли дети?", reply_markup=children_kb())


# ── Дети ─────────────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.children, F.data.startswith("children:"))
async def set_children(callback: CallbackQuery, state: FSMContext):
    value = int(callback.data.split(":")[1])
    await state.update_data(children=value)

    if value > 0:
        await state.set_state(TourWizard.children_ages)
        await callback.message.edit_text(
            f"👶 Укажите возраст {'ребёнка' if value == 1 else 'детей'} через запятую\n_Например: 3, 7_",
            parse_mode="Markdown"
        )
    else:
        await state.set_state(TourWizard.nights)
        await callback.message.edit_text("🌙 На сколько ночей?", reply_markup=nights_kb())


@router.message(TourWizard.children_ages)
async def set_children_ages(message: Message, state: FSMContext):
    await state.update_data(children_ages=message.text)
    await state.set_state(TourWizard.nights)
    await message.answer("🌙 На сколько ночей?", reply_markup=nights_kb())


# ── Ночей ─────────────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.nights, F.data.startswith("nights:"))
async def set_nights(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(nights=value)
    await state.set_state(TourWizard.budget)
    await callback.message.edit_text("💰 Бюджет на человека?", reply_markup=budget_kb())


# ── Бюджет ────────────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.budget, F.data.startswith("budget:"))
async def set_budget(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(budget=value)
    await state.set_state(TourWizard.meal)
    await callback.message.edit_text("🍽 Предпочтения по питанию?", reply_markup=meal_kb())


# ── Питание ───────────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.meal, F.data.startswith("meal:"))
async def set_meal(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(meal=value)
    await state.set_state(TourWizard.phone)
    await callback.message.edit_text(
        "📱 Оставьте номер телефона — менеджер свяжется с вами с готовой подборкой!\n\n_Например: +375291234567_",
        parse_mode="Markdown"
    )


# ── Телефон ───────────────────────────────────────────────────────────────────

@router.message(TourWizard.phone)
async def set_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await state.set_state(TourWizard.confirm)
    summary = build_summary(data)
    await message.answer(
        f"{summary}\nВсё верно? Отправляем заявку?",
        parse_mode="Markdown",
        reply_markup=confirm_kb()
    )


# ── Подтверждение ─────────────────────────────────────────────────────────────

@router.callback_query(TourWizard.confirm, F.data == "request:confirm")
async def confirm_request(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        await create_tour_request(session, callback.from_user.id, {
            "destination": data.get("destination"),
            "departure_date": data.get("departure_date"),
            "adults": data.get("adults", 2),
            "children": data.get("children", 0),
            "children_ages": data.get("children_ages"),
            "nights": data.get("nights"),
            "budget": data.get("budget"),
            "meal": data.get("meal"),
            "rest_type": data.get("rest_type"),
            "comment": data.get("phone"),
        })

        # Сохраняем в историю поиска
        await save_search_history(session, callback.from_user.id, {
            "destination": data.get("destination"),
            "departure_date": data.get("departure_date"),
            "adults": data.get("adults", 2),
            "children": data.get("children", 0),
            "nights": data.get("nights"),
            "budget": data.get("budget"),
            "meal": data.get("meal"),
        })

        # Обновляем предпочтения пользователя
        await update_user_preferences(session, callback.from_user.id,
            preferred_destinations=data.get("destination"),
            preferred_budget=data.get("budget"),
            preferred_rest_type=data.get("rest_type"),
            adults_default=data.get("adults", 2),
            children_default=data.get("children", 0),
        )

    await callback.message.edit_text(
        "✅ *Заявка принята!*\n\n"
        "Менеджер свяжется с вами в ближайшее время с готовой подборкой туров 🌴\n\n"
        "Если хотите — можете сразу написать Анне: @annagreentravel",
        parse_mode="Markdown"
    )


@router.callback_query(TourWizard.confirm, F.data == "request:restart")
async def restart_wizard(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(TourWizard.rest_type)
    await callback.message.edit_text(
        "✈️ Начнём заново! Какой отдых вас интересует?",
        reply_markup=rest_type_kb()
    )
