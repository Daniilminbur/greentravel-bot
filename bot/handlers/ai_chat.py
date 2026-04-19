import os
import tempfile
import httpx
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Voice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.gpt import chat_with_gpt, extract_request_data, clean_response
from bot.database.crud import create_tour_request, save_search_history, async_session
from bot.keyboards.main_menu import main_menu_kb
from bot.config import settings

router = Router()


class AIChat(StatesGroup):
    chatting = State()


MENU_BUTTONS = [
    "🔍 Подобрать тур", "🔥 Горящие туры", "📬 Подписка на горящие",
    "❤️ Избранное", "🕐 История поиска", "⭐ Отзывы",
    "📢 Наш канал", "💬 Связь с менеджером", "📞 Контакты", "🤖 Подобрать с ИИ"
]


async def transcribe_voice(bot, voice: Voice) -> str:
    """Скачиваем голосовое и отправляем в Whisper"""
    if not settings.OPENAI_API_KEY:
        return ""

    # Скачиваем файл
    file = await bot.get_file(voice.file_id)
    file_path = file.file_path

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await bot.download_file(file_path, tmp_path)

        # Отправляем в Whisper
        async with httpx.AsyncClient(timeout=30) as client:
            with open(tmp_path, "rb") as audio_file:
                resp = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    data={"model": "whisper-1", "language": "ru"},
                    files={"file": ("voice.ogg", audio_file, "audio/ogg")},
                )
            data = resp.json()
            return data.get("text", "")
    except Exception as e:
        print(f"[Whisper] Ошибка: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


async def process_message(message: Message, state: FSMContext, text: str):
    """Общая логика обработки сообщения (текст или голос)"""
    await message.bot.send_chat_action(message.chat.id, "typing")

    data = await state.get_data()
    messages = data.get("messages", [])
    messages.append({"role": "user", "content": text})

    if len(messages) > 20:
        messages = messages[-20:]

    gpt_response = await chat_with_gpt(messages)
    request_data = extract_request_data(gpt_response)
    clean_text = clean_response(gpt_response)

    messages.append({"role": "assistant", "content": gpt_response})
    await state.update_data(messages=messages)

    if request_data:
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

        await message.answer(clean_text, parse_mode="Markdown")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать Анне сейчас", url="https://t.me/annagreentravel")],
            [InlineKeyboardButton(text="🔄 Подобрать другой тур", callback_data="ai:restart")],
        ])
        await message.answer(
            "✅ *Заявка сохранена!*\n\nАнна свяжется с вами в ближайшее время 🌴",
            parse_mode="Markdown",
            reply_markup=kb
        )
        await state.clear()
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Выйти из чата", callback_data="ai:exit")]
        ])
        await message.answer(clean_text, parse_mode="Markdown", reply_markup=kb)


# ── Запуск ───────────────────────────────────────────────────────────────────

@router.message(F.text == "🤖 Подобрать с ИИ")
@router.message(F.text == "/ai")
async def start_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AIChat.chatting)
    await state.update_data(messages=[])
    await message.answer(
        "🤖 *ИИ-помощник Green Travel*\n\n"
        "Привет! Расскажи мне о своей мечте об отдыхе — "
        "и я помогу подобрать идеальный тур! 🌴\n\n"
        "Можешь написать текстом или записать голосовое 🎤",
        parse_mode="Markdown"
    )


# ── Текстовые сообщения ───────────────────────────────────────────────────────

@router.message(AIChat.chatting, F.text)
async def handle_text(message: Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        await state.clear()
        return
    await process_message(message, state, message.text)


# ── Голосовые сообщения ───────────────────────────────────────────────────────

@router.message(AIChat.chatting, F.voice)
async def handle_voice(message: Message, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Показываем что обрабатываем
    processing = await message.answer("🎤 Распознаю голосовое...")

    text = await transcribe_voice(message.bot, message.voice)

    await processing.delete()

    if not text:
        await message.answer("⚠️ Не удалось распознать голосовое. Попробуйте написать текстом.")
        return

    # Показываем что распознали
    await message.answer(f"🎤 _Распознано:_ {text}", parse_mode="Markdown")

    # Обрабатываем как обычное сообщение
    await process_message(message, state, text)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "ai:restart")
async def ai_restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AIChat.chatting)
    await state.update_data(messages=[])
    await callback.message.answer(
        "🔄 Начнём заново! Куда мечтаешь поехать?\n\nМожешь написать или записать голосовое 🎤"
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
