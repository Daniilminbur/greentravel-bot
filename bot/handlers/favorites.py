from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.crud import get_favorites, remove_favorite, async_session

router = Router()


@router.message(F.text == "❤️ Избранное")
async def show_favorites(message: Message):
    async with async_session() as session:
        favs = await get_favorites(session, message.from_user.id)

    if not favs:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔍 Подобрать тур", callback_data="go:search")
        ]])
        await message.answer(
            "❤️ *Избранное пусто*\n\n"
            "Здесь будут туры которые вы сохранили.\n"
            "Подберите тур и добавьте его в избранное!",
            parse_mode="Markdown",
            reply_markup=kb
        )
        return

    await message.answer(f"❤️ *Ваше избранное* ({len(favs)} туров):", parse_mode="Markdown")

    for fav in favs:
        text = (
            f"🌍 *{fav.destination}*\n"
            f"🏨 {fav.hotel or '—'}\n"
            f"✈️ {fav.fly_date or '—'} | 🌙 {fav.nights or '—'} ночей\n"
            f"🍽 {fav.meal or '—'}\n"
            f"💰 {fav.price or '—'} {fav.currency or ''}\n"
            f"🏢 {fav.operator or '—'}"
        )

        builder = InlineKeyboardBuilder()
        if fav.tour_url:
            builder.button(text="🔗 Смотреть тур", url=fav.tour_url)
        builder.button(text="🗑 Удалить", callback_data=f"fav:del:{fav.id}")
        builder.adjust(1)

        await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("fav:del:"))
async def delete_favorite(callback: CallbackQuery):
    fav_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        await remove_favorite(session, fav_id, callback.from_user.id)

    await callback.message.delete()
    await callback.answer("🗑 Удалено из избранного")


@router.callback_query(F.data == "go:search")
async def go_search(callback: CallbackQuery, state: FSMContext):
    from bot.keyboards.main_menu import rest_type_kb
    from bot.handlers.tour_search import TourWizard
    await state.set_state(TourWizard.rest_type)
    await callback.message.edit_text(
        "✈️ Какой отдых вас интересует?",
        reply_markup=rest_type_kb()
    )
