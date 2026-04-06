"""LLM + tool calling (OpenAI Chat Completions)."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

import config
from agent.tools import TOOL_DEFINITIONS, execute_tool


def chat_with_tools(
    messages: list[dict[str, Any]],
    tools: list | None = None,
    tool_context: dict[str, Any] | None = None,
) -> str:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("Задайте OPENAI_API_KEY в .env для ассистента.")

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.OPENAI_MODEL
    tools = tools or TOOL_DEFINITIONS
    msgs: list[dict[str, Any]] = [dict(m) for m in messages]

    for _ in range(12):
        resp = client.chat.completions.create(
            model=model,
            messages=msgs,
            tools=tools,
            tool_choice="auto",
        )
        choice = resp.choices[0]
        msg = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            msgs.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = execute_tool(tc.function.name, args, tool_context)
                msgs.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            continue

        return (msg.content or "").strip()

    return "Превышено число шагов с инструментами — упростите вопрос."
