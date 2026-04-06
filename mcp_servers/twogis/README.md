# MCP: 2GIS

Реализовано: **stdio** FastMCP. Данные: **API** при `TWO_GIS_API_KEY`, иначе **парсинг HTML** поиска 2gis.kz (httpx). Опционально только браузер: `TWO_GIS_USE_PLAYWRIGHT=1` и `playwright install chromium`.

Инструмент: **`search_restaurants(query, location="Алматы")`** → список заведений (название, адрес, рейтинг, телефон, часы).

Запуск из корня проекта:

```bash
python mcp_servers/twogis/server.py
```
