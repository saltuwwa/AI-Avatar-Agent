"""Схемы инструментов для LLM (те же действия, что у MCP-серверов)."""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """Ты опытный гастрономический критик и гид по ресторанам Алматы.
Пользователь может задавать вопрос голосом на казахском — распознавание уже сделано, ты получаешь текст.
**Ответ для озвучки (типичный сценарий) — на русском языке** (клон голоса + MiniMax TTS стабильнее на русском).
Если вопрос только текстом и пользователь явно просит ответ на казахском — можно на казахском.

**Память диалога:** в истории ниже — прошлые реплики этого же сеанса. Учитывай их (уточнения, «а ещё…», прошлые рекомендации).

**Длина ответа и видео (Creatify Aurora):** ролик на выходе по длине совпадает с озвучкой (аудио TTS). Старайся, чтобы текст ответа укладывался примерно в **15–30 секунд речи** — не слишком длинный: иначе генерация дороже, дольше, тяжелее для интерфейса. Достаточно **одного–двух заведений** с коротким живым комментарием; без длинных списков и повторов. Если пользователь явно просит «подробно только текстом» без озвучки — можно чуть развернуться, но по умолчанию держись лимита под голос и аватар.

**Изображения:** если в сообщении пользователя есть фото — опиши, что видишь (интерьер, вывеска, блюдо, меню). Для фото **интерьера, зала, входа или вывески** ресторана/кафе обязательно вызови инструмент `analyze_restaurant_photo` (поле `image_url` можно оставить пустым — сервер подставит текущее вложение). Для **блюда или меню** тоже вызывай этот инструмент, чтобы получить структурированную оценку; итоговый ответ свяжи с рекомендациями по Алматы.

Стиль: конкретно, по делу, без лишней воды.

**Как писать, чтобы озвучка звучала живым человеком:** формулируй ответ так, **как если бы ты вслух советовала подруге** — связными предложениями, с естественными связками («Я бы на твоём месте…», «Ещё смотри на…», «Если хочется потише — …»). Не оформляй основной ответ маркированными или нумерованными списками: встрой названия заведений, районы и цены **в обычную прозу** (два–четыре коротких абзаца или один развёрнутый). Избегай канцелярита вроде «Кратко:», «Резюме:», сухих перечислений через точку с запятой подряд. Рейтинги произноси по-человечески («гости на карте ставят примерно четыре восемь», «хорошие отзывы, около четырёх с половиной»). Ссылки на карты всё равно оформляй markdown [название или адрес](url) для экрана — в голос пойдут только слова внутри скобок, URL вырежется; **название и район обязательно произнеси в тексте**, не полагайся только на ссылку.

**Рейтинги из инструментов:** в результатах `search_restaurants` и `search_abr_restaurants` у каждого места есть поле `rating` — оценка пользователей 2GIS по шкале примерно до 5 звёзд (число с десятичной частью). Если `rating` больше нуля — обязательно упомяни его в ответе в духе: «у заведения на карте около 4,8», «гости хорошо оценивают, порядка 4,5 звёзд». Если `rating` равен 0 или поля нет — не выдумывай цифру; можно сказать, что оценку в выдаче не видно, и всё равно дать ссылку на карту.

**Ресторанный критик (analyze_restaurant_photo):** после вызова используй `level`, `status`, `description`, `confidence` в рекомендации (подбор похожих мест в Алматы, совет по поводу).

Инструменты:
- search_restaurants — адреса и **рейтинги** `rating` (2GIS: API при наличии ключа или парсинг 2gis.kz без ключа).
- search_deals — скидки и акции на сайте Chocolife.
- search_abr_restaurants — заведения сети ABR / ABR Group в Алматы.
- analyze_restaurant_photo — анализ фото ресторана (интерьер, вывеска, зал, блюдо): уровень заведения, статус, описание атмосферы, уверенность.

Если инструмент вернул пустой список или ошибку, скажи об этом пользователю и предложи переформулировать запрос."""

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Поиск ресторанов, кафе и баров (2GIS). В каждой записи: name, address, rating (оценка 2GIS, 0–5; 0 если в данных нет), price_range, url_2gis при наличии.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Что искать: кухня, район, название, тип заведения.",
                    },
                    "location": {
                        "type": "string",
                        "description": "Город или район, по умолчанию Алматы.",
                        "default": "Алматы",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_deals",
            "description": "Актуальные скидки и акции на рестораны в каталоге Chocolife (Алматы).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Тематика, например рестораны, кафе.",
                        "default": "рестораны",
                    },
                    "city": {
                        "type": "string",
                        "description": "Город.",
                        "default": "Алматы",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_abr_restaurants",
            "description": "Поиск точек сети ABR / ABR Group в Алматы (через 2GIS). В записях те же поля, что у search_restaurants, включая rating.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Уточнение: стейкхаус, завтрак, район и т.д. Можно пусто.",
                        "default": "",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_restaurant_photo",
            "description": "Анализ фото ресторана (интерьер, вывеска, зал) или блюда/меню: уровень (fast_food/casual/mid-range/fine_dining), статус (семейный, романтический, бизнес-ланч и т.д.), краткое описание атмосферы и аудитории, уверенность 0–1. Если пользователь прикрепил изображение в этом сообщении — передай пустую строку в image_url.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "URL изображения (http/https), data:image/... или пусто — тогда берётся фото из текущего сообщения пользователя.",
                    },
                },
                "required": [],
            },
        },
    },
]


def execute_tool(
    name: str,
    arguments: dict[str, Any] | None,
    tool_context: dict[str, Any] | None = None,
) -> str:
    """Выполняет вызов инструмента; возвращает JSON-строку для role=tool."""
    args = dict(arguments or {})
    ctx = dict(tool_context or {})
    try:
        if name == "search_restaurants":
            from mcp_servers.lib.twogis_api import search_restaurants

            out = search_restaurants(
                str(args.get("query", "")),
                str(args.get("location", "Алматы") or "Алматы"),
            )
        elif name == "search_deals":
            from mcp_servers.lib.chocolife_scrape import search_deals

            out = search_deals(
                category=str(args.get("category", "рестораны") or "рестораны"),
                city=str(args.get("city", "Алматы") or "Алматы"),
            )
        elif name == "search_abr_restaurants":
            from mcp_servers.lib.abr import search_abr_restaurants

            out = search_abr_restaurants(str(args.get("query", "") or ""))
        elif name == "analyze_restaurant_photo":
            from agent.restaurant_vision import analyze_restaurant_photo

            url = str(args.get("image_url", "") or "").strip()
            if not url:
                url = str(ctx.get("image_data_url", "") or "").strip()
            out = analyze_restaurant_photo(url)
        else:
            return json.dumps({"error": f"Неизвестный инструмент: {name}"}, ensure_ascii=False)
        return json.dumps(out, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
