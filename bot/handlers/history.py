from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.crud import get_search_history, async_session

router = Router()

DATE_LABELS = {
    "2weeks": "В ближайшие 2 недели",
    "1month": "Через месяц",
    "2-3months": "Через 2–3 месяца",
    "3months+": "Более чем через 3 месяца",
    "flexible": "Гибкая дата",
}


@router.message(F.text == "🕐 История поиска")
async def show_history(message: Message):
    async with async_session() as session:
        history = await get_search_history(session, message.from_user.id)

    if not history:
        await message.answer(
            "🕐 *История поиска пуста*\n\nПодберите первый тур — и он появится здесь!",
            parse_mode="Markdown"
        )
        return

    await message.answer(f"🕐 *Ваши последние поиски:*", parse_mode="Markdown")

    for i, h in enumerate(history, 1):
        date_label = DATE_LABELS.get(h.departure_date, h.departure_date or "—")
        text = (
            f"*{i}. {h.destination or '—'}*\n"
            f"📅 {date_label}\n"
            f"👥 {h.adults} взр"
            + (f" + {h.children} дет" if h.children else "") +
            f" | 🌙 {h.nights or '—'} ночей\n"
            f"💰 {h.budget or '—'}"
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Повторить этот поиск", callback_data=f"history:repeat:{h.id}")
        builder.adjust(1)

        await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("history:repeat:"))
async def repeat_search(callback: CallbackQuery, state: FSMContext):
    history_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        history = await get_search_history(session, callback.from_user.id)

    item = next((h for h in history if h.id == history_id), None)
    if not item:
        await callback.answer("Поиск не найден")
        return

    from bot.handlers.tour_search import TourWizard
    await state.update_data(
        rest_type="any",
        destination=item.destination,
        departure_date=item.departure_date,
        adults=item.adults,
        children=item.children,
        nights=item.nights,
        budget=item.budget,
        meal=item.meal,
    )
    await state.set_state(TourWizard.phone)
    await callback.message.edit_text(
        f"🔄 *Повторяем поиск:*\n\n"
        f"🌍 {item.destination or '—'} | 💰 {item.budget or '—'}\n\n"
        f"📱 Укажите ваш телефон:",
        parse_mode="Markdown"
    )
    await callback.answer()
