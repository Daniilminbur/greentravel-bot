import httpx
import json
from bot.config import settings

SYSTEM_PROMPT = """Ты — умный ИИ-помощник турагентства Green Travel (Беларусь).
Менеджер — Анна, контакт @annagreentravel, сайт greentravel.by.

Твоя задача — вести диалог с клиентом и собрать информацию для подбора тура:
1. Направление (куда хочет поехать)
2. Даты или период вылета
3. Количество взрослых и детей (с возрастом детей)
4. Количество ночей
5. Бюджет на человека
6. Тип питания (всё включено, завтраки, без разницы)
7. Номер телефона для связи

Правила:
- Веди диалог естественно, как живой менеджер
- Задавай по 1-2 вопроса за раз, не засыпай всем списком
- Работаешь с направлениями: Турция, Египет, ОАЭ, Таиланд, Греция, Мальдивы, Испания, Бали, Кипр
- Вылеты только из Минска (Беларусь)
- Валюта — доллары США
- Не называй конкретные цены — они меняются ежедневно
- Отвечай на любые вопросы о туризме: визы, климат, отели, страховки
- Если клиент готов оставить заявку — скажи что передашь менеджеру и попроси телефон
- Будь дружелюбным, используй эмодзи умеренно
- Отвечай на русском языке

Когда собрал все данные (направление + даты + туристы + бюджет + телефон) — 
напиши в конце сообщения специальный тег: [READY_FOR_REQUEST]
и следом JSON с данными:
{"destination": "...", "departure_date": "...", "adults": N, "children": N, "nights": "...", "budget": "...", "meal": "...", "phone": "..."}

Если клиент спрашивает что-то не связанное с туризмом — вежливо объясни что ты помощник турагентства.
"""


async def chat_with_gpt(messages: list[dict]) -> str:
    """Отправляем историю диалога в GPT и получаем ответ"""
    if not settings.OPENAI_API_KEY:
        return "❌ GPT не настроен. Обратитесь к администратору."

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Ошибка GPT: {e}. Напишите менеджеру @annagreentravel"


def extract_request_data(gpt_response: str) -> dict | None:
    """Извлекаем данные заявки из ответа GPT если она готова"""
    if "[READY_FOR_REQUEST]" not in gpt_response:
        return None
    try:
        json_start = gpt_response.find("{", gpt_response.find("[READY_FOR_REQUEST]"))
        json_end = gpt_response.rfind("}") + 1
        json_str = gpt_response[json_start:json_end]
        return json.loads(json_str)
    except Exception:
        return None


def clean_response(gpt_response: str) -> str:
    """Убираем служебные теги из ответа перед отправкой пользователю"""
    if "[READY_FOR_REQUEST]" in gpt_response:
        return gpt_response[:gpt_response.find("[READY_FOR_REQUEST]")].strip()
    return gpt_response.strip()
