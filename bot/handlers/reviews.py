from aiogram import Router, F
from aiogram.types import Message
from bot.database.crud import get_active_reviews, async_session

router = Router()

STAR_MAP = {5: "⭐⭐⭐⭐⭐", 4: "⭐⭐⭐⭐", 3: "⭐⭐⭐", 2: "⭐⭐", 1: "⭐"}


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    async with async_session() as session:
        reviews = await get_active_reviews(session)

    if not reviews:
        await message.answer(
            "⭐ *Отзывы*\n\nПока отзывов нет — будьте первым! 😊\n\n"
            "После поездки напишите нам и мы добавим ваш отзыв.",
            parse_mode="Markdown"
        )
        return

    # Показываем по 3 последних отзыва
    for review in reviews[:3]:
        stars = STAR_MAP.get(review.rating, "⭐⭐⭐⭐⭐")
        dest = f" — {review.destination}" if review.destination else ""
        text = (
            f"{stars}\n"
            f"*{review.author_name}*{dest}\n\n"
            f"_{review.text}_"
        )
        await message.answer(text, parse_mode="Markdown")

    if len(reviews) > 3:
        await message.answer(f"_...и ещё {len(reviews) - 3} отзывов. Приходите к нам — убедитесь сами! 🌴_",
                             parse_mode="Markdown")
