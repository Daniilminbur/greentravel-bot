from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.main_menu import subscription_destinations_kb, budget_kb
from bot.database.crud import create_subscription, async_session

router = Router()


class SubWizard(StatesGroup):
    destination = State()
    budget = State()


@router.message(F.text == "📬 Подписка на горящие")
async def start_subscription(message: Message, state: FSMContext):
    await state.set_state(SubWizard.destination)
    await message.answer(
        "🔔 *Подписка на горящие туры*\n\n"
        "Выберите направление — и я буду присылать вам лучшие горящие предложения! 🔥",
        parse_mode="Markdown",
        reply_markup=subscription_destinations_kb()
    )


@router.callback_query(SubWizard.destination, F.data.startswith("sub_dest:"))
async def set_sub_destination(callback: CallbackQuery, state: FSMContext):
    destination = callback.data.split(":")[1]
    await state.update_data(destination=destination)
    await state.set_state(SubWizard.budget)
    await callback.message.edit_text(
        f"🌍 Направление: *{destination}*\n\n💰 Максимальный бюджет на человека?",
        parse_mode="Markdown",
        reply_markup=budget_kb()
    )


@router.callback_query(SubWizard.budget, F.data.startswith("budget:"))
async def set_sub_budget(callback: CallbackQuery, state: FSMContext):
    budget_raw = callback.data.split(":")[1]
    data = await state.get_data()
    await state.clear()

    # Парсим числовой бюджет
    budget_num = None
    if budget_raw not in ("flexible", "2000+"):
        try:
            budget_num = int(budget_raw)
        except ValueError:
            pass

    async with async_session() as session:
        await create_subscription(
            session,
            telegram_id=callback.from_user.id,
            destination=data["destination"],
            budget_max=budget_num,
        )

    dest = data["destination"]
    budget_label = "любой" if budget_raw in ("flexible", "2000+") else f"до ${budget_raw}"

    await callback.message.edit_text(
        f"✅ *Подписка оформлена!*\n\n"
        f"🌍 Направление: {dest}\n"
        f"💰 Бюджет: {budget_label}\n\n"
        f"Как только появятся горящие предложения — сразу пришлю! 🔥\n\n"
        f"_Отписаться можно командой /unsubscribe_",
        parse_mode="Markdown"
    )
