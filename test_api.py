"""
Запусти этот скрипт чтобы проверить доступные endpoints Tourvisor API.
Результат увидишь в логах Railway.

Добавь в bot/main.py вызов: await test_tourvisor_api()
"""
import httpx

AUTHKEY = "17064558ef0702a10524e99e73e712cc93c8fb"

async def test_tourvisor_api():
    endpoints = [
        ("Заявки (orders)", f"https://tourvisor.ru/xml/orders.php?authkey={AUTHKEY}&format=json&limit=1"),
        ("Горящие туры (hottours)", f"https://tourvisor.ru/xml/hottours.php?authkey={AUTHKEY}&format=json&limit=1"),
        ("Горящие v2", f"https://tourvisor.ru/xml/hot.php?authkey={AUTHKEY}&format=json&limit=1"),
        ("Поиск туров", f"https://tourvisor.ru/xml/search.php?authkey={AUTHKEY}&format=json"),
    ]

    async with httpx.AsyncClient(timeout=10) as client:
        for name, url in endpoints:
            try:
                resp = await client.get(url)
                print(f"[API TEST] {name}: HTTP {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.text[:200]
                    print(f"[API TEST] Ответ: {data}")
                else:
                    print(f"[API TEST] Ошибка: {resp.text[:100]}")
            except Exception as e:
                print(f"[API TEST] {name}: Ошибка — {e}")
