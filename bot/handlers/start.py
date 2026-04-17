from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import main_menu_kb, destinations_kb, subscription_destinations_kb
from bot.database.crud import get_or_create_user, get_active_subscriptions, deactivate_subscription
from bot.database.crud import async_session
from bot.config import settings

router = Router()

WELCOME_TEXT = """
👋 Привет! Я бот турагентства *Green Travel*

Помогу подобрать тур мечты, расскажу о горящих предложениях и свяжу с менеджером 🌴

Выбери что тебя интересует 👇
"""

HELP_TEXT = """
ℹ️ *Команды бота:*

✈️ /tour — подобрать тур
🔥 /hot — горящие туры
🔔 /subscribe — подписка на горящие
🔕 /unsubscribe — отписаться
📞 /contacts — наши контакты
⭐ /reviews — отзывы клиентов
❌ /cancel — отменить текущее действие

💬 По всем вопросам: @annagreentravel
"""

CONTACTS_TEXT = """
📞 *Контакты Green Travel*

👩 Анна — менеджер по турам
├ @annagreentravel
├ +375 25 974-37-18
├ +375 33 900-69-89
└ +375 33 324-30-92

🌐 Сайт: greentravel.by
📢 Канал: @curlytravelagent

🕐 Работаем: Пн–Пт 9:00–19:00, Сб 10:00–17:00
"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        if param.startswith("sub_"):
            destination = param.replace("sub_", "").replace("_", " ")
            await state.set_state("SubWizard:budget")
            await state.update_data(destination=destination)
            from bot.keyboards.main_menu import budget_kb
            await message.answer(
                f"🔔 Подписка на горящие туры\n\n🌍 Направление: *{destination}*\n\n💰 Максимальный бюджет на человека?",
                parse_mode="Markdown",
                reply_markup=budget_kb()
            )
            return
        elif param.startswith("tour"):
            await state.set_state("TourWizard:destination")
            await message.answer(
                "✈️ Давай подберём тур! Куда хотите поехать?",
                parse_mode="Markdown",
                reply_markup=destinations_kb()
            )
            return

    await message.answer(WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="Markdown")


@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять 🙂", reply_markup=main_menu_kb())
        return
    await state.clear()
    await message.answer("❌ Действие отменено. Возвращаемся в главное меню.", reply_markup=main_menu_kb())


@router.message(Command("tour"))
async def cmd_tour(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state("TourWizard:destination")
    await message.answer(
        "✈️ *Подбор тура*\n\nКуда хотите поехать?",
        parse_mode="Markdown",
        reply_markup=destinations_kb()
    )


@router.message(Command("hot"))
@router.message(F.text == "🔥 Горящие туры")
async def cmd_hot(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Смотреть горящие туры", url="https://greentravel.by")],
        [InlineKeyboardButton(text="🔔 Подписаться на уведомления", callback_data="start_subscribe")],
    ])
    await message.answer(
        "🔥 *Горящие туры*\n\n"
        "Актуальные предложения со скидками до 50% — на сайте обновляются каждый день!\n\n"
        "Или подпишитесь — я сам пришлю когда появится что-то интересное 👇",
        parse_mode="Markdown",
        reply_markup=kb
    )


@router.message(Command("subscribe"))
@router.message(F.text == "📬 Подписка на горящие")
async def cmd_subscribe(message: Message, state: FSMContext):
    await state.set_state("SubWizard:destination")
    await message.answer(
        "🔔 *Подписка на горящие туры*\n\nВыберите направление — буду присылать лучшие предложения! 🔥",
        parse_mode="Markdown",
        reply_markup=subscription_destinations_kb()
    )


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    async with async_session() as session:
        subs = await get_active_subscriptions(session)
        user_subs = [s for s in subs if s.telegram_id == message.from_user.id]

        if not user_subs:
            await message.answer(
                "У вас нет активных подписок.\n\nЧтобы подписаться — нажмите 📬 *Подписка на горящие*",
                parse_mode="Markdown"
            )
            return

        for sub in user_subs:
            await deactivate_subscription(session, sub.id)

    await message.answer(
        f"✅ Отписались от {len(user_subs)} подписок на горящие туры.\n\n"
        "Когда захотите снова — нажмите 📬 *Подписка на горящие*",
        parse_mode="Markdown"
    )


@router.message(Command("contacts"))
@router.message(F.text == "📞 Контакты")
async def cmd_contacts(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать Анне", url="https://t.me/annagreentravel")],
        [InlineKeyboardButton(text="🌐 Перейти на сайт", url="https://greentravel.by")],
    ])
    await message.answer(CONTACTS_TEXT, parse_mode="Markdown", reply_markup=kb)


@router.message(Command("reviews"))
async def cmd_reviews(message: Message):
    from bot.handlers.reviews import show_reviews
    await show_reviews(message)


@router.message(F.text == "📢 Наш канал")
async def our_channel(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📢 Открыть канал", url="https://t.me/curlytravelagent")
    ]])
    await message.answer(
        "📢 Подписывайтесь на канал!\n\nАнна каждый день публикует горящие туры и выгодные предложения 🔥",
        reply_markup=kb
    )


@router.message(F.text == "💬 Связь с менеджером")
async def contact_manager(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💬 Написать Анне", url="https://t.me/annagreentravel")
    ]])
    await message.answer(
        "💬 *Связь с менеджером*\n\nАнна ответит на все вопросы и поможет с выбором тура!\n\nОбычно отвечает в течение 15–30 минут 🙂",
        parse_mode="Markdown",
        reply_markup=kb
    )


@router.callback_query(F.data == "start_subscribe")
async def cb_start_subscribe(callback, state: FSMContext):
    await state.set_state("SubWizard:destination")
    await callback.message.edit_text(
        "🔔 *Подписка на горящие туры*\n\nВыберите направление:",
        parse_mode="Markdown",
        reply_markup=subscription_destinations_kb()
    )
