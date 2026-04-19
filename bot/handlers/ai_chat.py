from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.gpt import chat_with_gpt, extract_request_data, clean_response
from bot.database.crud import create_tour_request, save_search_history, async_session
from bot.keyboards.main_menu import main_menu_kb

router = Router()


class AIChat(StatesGroup):
    chatting = State()


# История диалога хранится в FSM state
# messages = [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]


@router.message(F.text == "🤖 Подобрать с ИИ")
@router.message(F.text == "/ai")
async def start_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AIChat.chatting)
    await state.update_data(messages=[])

    await message.answer(
        "🤖 *ИИ-помощник Green Travel*\n\n"
        "Привет! Я умный помощник — расскажи мне о своей мечте об отдыхе, "
        "и я помогу подобрать идеальный тур! 🌴\n\n"
        "Куда мечтаешь поехать? Или просто опиши что хочешь — море, горы, экскурсии?",
        parse_mode="Markdown"
    )


@router.message(AIChat.chatting)
async def handle_ai_message(message: Message, state: FSMContext):
    user_text = message.text

    # Кнопки меню — выходим из AI чата
    menu_buttons = ["🔍 Подобрать тур", "🔥 Горящие туры", "📬 Подписка на горящие",
                    "❤️ Избранное", "🕐 История поиска", "⭐ Отзывы",
                    "📢 Наш канал", "💬 Связь с менеджером", "📞 Контакты"]
    if user_text in menu_buttons:
        await state.clear()
        return

    # Показываем что печатаем
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Достаём историю диалога
    data = await state.get_data()
    messages = data.get("messages", [])

    # Добавляем сообщение пользователя
    messages.append({"role": "user", "content": user_text})

    # Ограничиваем историю — последние 20 сообщений
    if len(messages) > 20:
        messages = messages[-20:]

    # Отправляем в GPT
    gpt_response = await chat_with_gpt(messages)

    # Проверяем — готова ли заявка
    request_data = extract_request_data(gpt_response)
    clean_text = clean_response(gpt_response)

    # Добавляем ответ GPT в историю
    messages.append({"role": "assistant", "content": gpt_response})
    await state.update_data(messages=messages)

    if request_data:
        # GPT собрал все данные — создаём заявку!
        async with async_session() as session:
            await create_tour_request(session, message.from_user.id, {
                "destination": request_data.get("destination"),
                "departure_date": request_data.get("departure_date"),
                "adults": int(request_data.get("adults", 2)),
                "children": int(request_data.get("children", 0)),
                "nights": request_data.get("nights"),
                "budget": request_data.get("budget"),
                "meal": request_data.get("meal"),
                "comment": request_data.get("phone"),
                "rest_type": "any",
            })

            await save_search_history(session, message.from_user.id, {
                "destination": request_data.get("destination"),
                "adults": int(request_data.get("adults", 2)),
                "children": int(request_data.get("children", 0)),
                "nights": request_data.get("nights"),
                "budget": request_data.get("budget"),
            })

        # Отправляем финальное сообщение GPT
        await message.answer(clean_text, parse_mode="Markdown")

        # Подтверждение
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать Анне сейчас", url="https://t.me/annagreentravel")],
            [InlineKeyboardButton(text="🔄 Подобрать другой тур", callback_data="ai:restart")],
        ])
        await message.answer(
            "✅ *Заявка сохранена!*\n\n"
            "Анна свяжется с вами в ближайшее время с готовой подборкой 🌴",
            parse_mode="Markdown",
            reply_markup=kb
        )
        await state.clear()

    else:
        # Продолжаем диалог
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Выйти из чата", callback_data="ai:exit")]
        ])
        await message.answer(clean_text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(F.data == "ai:restart")
async def ai_restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AIChat.chatting)
    await state.update_data(messages=[])
    await callback.message.answer(
        "🔄 Начнём заново! Куда мечтаешь поехать?",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "ai:exit")
async def ai_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "👋 Вышли из ИИ-чата. Чем могу помочь?",
        reply_markup=main_menu_kb()
    )
    await callback.answer()
