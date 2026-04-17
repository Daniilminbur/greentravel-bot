from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, func, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Пользователи бота"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_blocked = Column(Boolean, default=False)

    # Персонализация
    preferred_destinations = Column(String(500), nullable=True)  # через запятую
    preferred_budget = Column(String(50), nullable=True)
    preferred_rest_type = Column(String(50), nullable=True)  # sea/mountains/excursions
    adults_default = Column(Integer, default=2)
    children_default = Column(Integer, default=0)

    subscriptions = relationship("HotTourSubscription", back_populates="user")
    requests = relationship("TourRequest", back_populates="user")
    favorites = relationship("FavoriteTour", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")


class TourRequest(Base):
    """Заявки на подбор тура (из квеста бота)"""
    __tablename__ = "tour_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(BigInteger, nullable=False)

    destination = Column(String(100), nullable=True)
    departure_date = Column(String(50), nullable=True)
    adults = Column(Integer, default=2)
    children = Column(Integer, default=0)
    children_ages = Column(String(50), nullable=True)
    nights = Column(String(50), nullable=True)
    budget = Column(String(100), nullable=True)
    meal = Column(String(50), nullable=True)
    rest_type = Column(String(50), nullable=True)  # тип отдыха
    comment = Column(Text, nullable=True)

    status = Column(String(20), default="new")  # new/in_progress/done/cancelled
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="requests")


class HotTourSubscription(Base):
    """Подписки на горящие туры"""
    __tablename__ = "hot_tour_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(BigInteger, nullable=False)

    destination = Column(String(100), nullable=False)
    budget_max = Column(Integer, nullable=True)
    adults = Column(Integer, default=2)
    children = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    last_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="subscriptions")


class TourvisorOrder(Base):
    """Заявки полученные через Tourvisor webhook"""
    __tablename__ = "tourvisor_orders"

    id = Column(Integer, primary_key=True)
    tourvisor_id = Column(String(50), unique=True)
    order_type = Column(Integer, default=0)

    client_name = Column(String(200), nullable=True)
    client_phone = Column(String(50), nullable=True)
    client_email = Column(String(200), nullable=True)

    country = Column(String(100), nullable=True)
    departure = Column(String(100), nullable=True)
    hotel = Column(String(200), nullable=True)
    fly_date = Column(String(50), nullable=True)
    nights = Column(String(20), nullable=True)
    price = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    meal = Column(String(100), nullable=True)
    placement = Column(String(100), nullable=True)
    operator = Column(String(100), nullable=True)
    comments = Column(Text, nullable=True)

    status = Column(String(20), default="new")
    assigned_to = Column(String(100), nullable=True)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Review(Base):
    """Отзывы"""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    author_name = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    rating = Column(Integer, default=5)
    destination = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class FavoriteTour(Base):
    """Избранные туры пользователя"""
    __tablename__ = "favorite_tours"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(BigInteger, nullable=False)

    # Данные тура
    destination = Column(String(100), nullable=False)
    hotel = Column(String(200), nullable=True)
    price = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    fly_date = Column(String(50), nullable=True)
    nights = Column(String(20), nullable=True)
    meal = Column(String(100), nullable=True)
    operator = Column(String(100), nullable=True)
    tour_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="favorites")


class SearchHistory(Base):
    """История поиска пользователя"""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(BigInteger, nullable=False)

    destination = Column(String(100), nullable=True)
    departure_date = Column(String(50), nullable=True)
    adults = Column(Integer, default=2)
    children = Column(Integer, default=0)
    nights = Column(String(50), nullable=True)
    budget = Column(String(100), nullable=True)
    meal = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="search_history")


class Notification(Base):
    """Очередь уведомлений"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    type = Column(String(50), nullable=False)  # hot_tour/price_drop/reminder
    message = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
