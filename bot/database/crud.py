from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, update, delete, text
from bot.config import settings
from bot.database.models import (
    Base, User, TourRequest, HotTourSubscription,
    TourvisorOrder, Review, FavoriteTour, SearchHistory, Notification
)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Добавляем новые колонки если их нет (миграция)
        await migrate_columns(conn)


async def migrate_columns(conn):
    """Добавляем новые колонки в существующие таблицы"""
    migrations = [
        # User — новые поля персонализации
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_destinations VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_budget VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_rest_type VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS adults_default INTEGER DEFAULT 2",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS children_default INTEGER DEFAULT 0",
        # TourRequest — новое поле
        "ALTER TABLE tour_requests ADD COLUMN IF NOT EXISTS rest_type VARCHAR(50)",
        # HotTourSubscription — новое поле
        "ALTER TABLE hot_tour_subscriptions ADD COLUMN IF NOT EXISTS last_notified_at TIMESTAMP",
    ]
    for sql in migrations:
        try:
            await conn.execute(text(sql))
        except Exception:
            pass  # Колонка уже есть или SQLite не поддерживает IF NOT EXISTS


# ── Users ──────────────────────────────────────────────────────────────────

async def get_or_create_user(session: AsyncSession, telegram_id: int,
                              username: str = None, full_name: str = None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_user_preferences(session: AsyncSession, telegram_id: int, **kwargs):
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(**kwargs)
    )
    await session.commit()


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).where(User.is_blocked == False))
    return result.scalars().all()


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


# ── TourRequests ───────────────────────────────────────────────────────────

async def create_tour_request(session: AsyncSession, telegram_id: int, data: dict) -> TourRequest:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    req = TourRequest(
        user_id=user.id if user else None,
        telegram_id=telegram_id,
        **data
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


async def get_new_requests(session: AsyncSession) -> list[TourRequest]:
    result = await session.execute(
        select(TourRequest).where(TourRequest.status == "new").order_by(TourRequest.created_at.desc())
    )
    return result.scalars().all()


async def update_request_status(session: AsyncSession, request_id: int,
                                 status: str, assigned_to: str = None):
    await session.execute(
        update(TourRequest).where(TourRequest.id == request_id)
        .values(status=status, assigned_to=assigned_to)
    )
    await session.commit()


# ── SearchHistory ──────────────────────────────────────────────────────────

async def save_search_history(session: AsyncSession, telegram_id: int, data: dict):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    history = SearchHistory(
        user_id=user.id if user else None,
        telegram_id=telegram_id,
        **data
    )
    session.add(history)

    old = await session.execute(
        select(SearchHistory)
        .where(SearchHistory.telegram_id == telegram_id)
        .order_by(SearchHistory.created_at.desc())
        .offset(10)
    )
    for old_item in old.scalars().all():
        await session.delete(old_item)

    await session.commit()


async def get_search_history(session: AsyncSession, telegram_id: int) -> list[SearchHistory]:
    result = await session.execute(
        select(SearchHistory)
        .where(SearchHistory.telegram_id == telegram_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(5)
    )
    return result.scalars().all()


# ── FavoriteTours ──────────────────────────────────────────────────────────

async def add_favorite(session: AsyncSession, telegram_id: int, data: dict) -> FavoriteTour:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    fav = FavoriteTour(
        user_id=user.id if user else None,
        telegram_id=telegram_id,
        **data
    )
    session.add(fav)
    await session.commit()
    await session.refresh(fav)
    return fav


async def get_favorites(session: AsyncSession, telegram_id: int) -> list[FavoriteTour]:
    result = await session.execute(
        select(FavoriteTour)
        .where(FavoriteTour.telegram_id == telegram_id)
        .order_by(FavoriteTour.created_at.desc())
    )
    return result.scalars().all()


async def remove_favorite(session: AsyncSession, fav_id: int, telegram_id: int):
    await session.execute(
        delete(FavoriteTour)
        .where(FavoriteTour.id == fav_id, FavoriteTour.telegram_id == telegram_id)
    )
    await session.commit()


# ── HotTourSubscriptions ───────────────────────────────────────────────────

async def create_subscription(session: AsyncSession, telegram_id: int,
                               destination: str, budget_max: int = None,
                               adults: int = 2, children: int = 0) -> HotTourSubscription:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    sub = HotTourSubscription(
        user_id=user.id if user else None,
        telegram_id=telegram_id,
        destination=destination,
        budget_max=budget_max,
        adults=adults,
        children=children,
    )
    session.add(sub)
    await session.commit()
    return sub


async def get_active_subscriptions(session: AsyncSession) -> list[HotTourSubscription]:
    result = await session.execute(
        select(HotTourSubscription).where(HotTourSubscription.is_active == True)
    )
    return result.scalars().all()


async def deactivate_subscription(session: AsyncSession, sub_id: int):
    await session.execute(
        update(HotTourSubscription).where(HotTourSubscription.id == sub_id).values(is_active=False)
    )
    await session.commit()


async def get_user_subscriptions(session: AsyncSession, telegram_id: int) -> list[HotTourSubscription]:
    result = await session.execute(
        select(HotTourSubscription)
        .where(HotTourSubscription.telegram_id == telegram_id, HotTourSubscription.is_active == True)
    )
    return result.scalars().all()


# ── TourvisorOrders ────────────────────────────────────────────────────────

async def save_tourvisor_order(session: AsyncSession, data: dict) -> TourvisorOrder | None:
    result = await session.execute(
        select(TourvisorOrder).where(TourvisorOrder.tourvisor_id == str(data.get("id")))
    )
    existing = result.scalar_one_or_none()
    if existing:
        return None

    order = TourvisorOrder(
        tourvisor_id=str(data.get("id")),
        order_type=int(data.get("type", 0) or 0),
        client_name=data.get("name", ""),
        client_phone=data.get("phone", ""),
        client_email=data.get("email", ""),
        country=data.get("country", ""),
        departure=data.get("departure", ""),
        hotel=data.get("hotel", ""),
        fly_date=data.get("flydate", ""),
        nights=data.get("nights", ""),
        price=data.get("price", ""),
        currency=data.get("currency", ""),
        meal=data.get("meal", ""),
        placement=data.get("placement", ""),
        operator=data.get("operator", ""),
        comments=data.get("comments", ""),
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_all_orders(session: AsyncSession, status: str = None) -> list[TourvisorOrder]:
    q = select(TourvisorOrder).order_by(TourvisorOrder.created_at.desc())
    if status:
        q = q.where(TourvisorOrder.status == status)
    result = await session.execute(q)
    return result.scalars().all()


# ── Reviews ────────────────────────────────────────────────────────────────

async def get_active_reviews(session: AsyncSession) -> list[Review]:
    result = await session.execute(
        select(Review).where(Review.is_active == True).order_by(Review.created_at.desc())
    )
    return result.scalars().all()


async def add_review(session: AsyncSession, author: str, text: str,
                     rating: int = 5, destination: str = None) -> Review:
    review = Review(author_name=author, text=text, rating=rating, destination=destination)
    session.add(review)
    await session.commit()
    return review


# ── Notifications ──────────────────────────────────────────────────────────

async def create_notification(session: AsyncSession, telegram_id: int,
                               type: str, message: str) -> Notification:
    notif = Notification(telegram_id=telegram_id, type=type, message=message)
    session.add(notif)
    await session.commit()
    return notif
