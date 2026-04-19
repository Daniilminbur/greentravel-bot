from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    ADMIN_BOT_TOKEN: str = ""        # если будет отдельный бот для админов
    CHANNEL_ID: str = "@curlytravelagent"
    ADMIN_IDS: list[int] = []        # список Telegram ID администраторов

    # База данных
    # Локально используется SQLite, на Railway — PostgreSQL
    DATABASE_URL: str = "sqlite+aiosqlite:///greentravel.db"

    # Tourvisor
    TOURVISOR_AUTHKEY: str = "17064558ef0702a10524e99e73e712cc93c8fb"
    TOURVISOR_WEBHOOK_SECRET: str = ""  # для верификации входящих webhook

    # Сайт
    SITE_URL: str = "https://greentravel.by"

    # Менеджер для уведомлений (Telegram ID Анны или общий чат)
    MANAGER_CHAT_ID: int = 0

    # Webhook сервер
    WEBHOOK_HOST: str = ""           # https://your-app.railway.app
    WEBHOOK_PATH: str = "/webhook/tourvisor"

    # OpenAI
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
