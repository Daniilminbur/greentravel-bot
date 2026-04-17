import httpx
from aiohttp import web
from bot.config import settings
from bot.database.crud import save_tourvisor_order, async_session

_bot = None

def set_bot(bot):
    global _bot
    _bot = bot


async def fetch_order_from_tourvisor(order_id: str, order_type: int = 0) -> dict | None:
    endpoint = "ordersonline" if order_type == 1 else "orders"
    url = f"https://tourvisor.ru/xml/{endpoint}.php"
    params = {"authkey": settings.TOURVISOR_AUTHKEY, "id": order_id, "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            orders = data.get("orders", {}).get("order", [])
            if isinstance(orders, list) and orders:
                return orders[0]
            elif isinstance(orders, dict):
                return orders
    except Exception as e:
        print(f"[Tourvisor] Ошибка: {e}")
    return None


async def handle_webhook(request: web.Request) -> web.Response:
    order_id = request.rel_url.query.get("id")
    order_type = int(request.rel_url.query.get("type", 0))
    if not order_id:
        return web.Response(text="ok")

    order_data = await fetch_order_from_tourvisor(order_id, order_type)
    if not order_data:
        return web.Response(text="ok")

    async with async_session() as session:
        await save_tourvisor_order(session, order_data)

    # Заявка сохранена в БД — видна в веб-панели, уведомление в Telegram не нужно
    return web.Response(text="ok")


async def poll_tourvisor_orders(bot, last_id: int = 0) -> int:
    url = "https://tourvisor.ru/xml/orders.php"
    params = {"authkey": settings.TOURVISOR_AUTHKEY, "format": "json", "limit": 20}
    if last_id:
        params["lastid"] = last_id

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            orders = data.get("orders", {}).get("order", [])
            if isinstance(orders, dict):
                orders = [orders]
            for order in orders:
                async with async_session() as session:
                    await save_tourvisor_order(session, order)
                last_id = max(last_id, int(order.get("id", 0)))
    except Exception as e:
        print(f"[Tourvisor] Ошибка поллинга: {e}")

    return last_id


def create_webhook_app() -> web.Application:
    app = web.Application()
    app.router.add_get(settings.WEBHOOK_PATH, handle_webhook)
    return app
