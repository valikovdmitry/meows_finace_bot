"""Private HTTP API for sending bot notifications to the primary chat."""

import secrets

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from telegram import Bot

from config import BOT_API_KEY, TOKEN
from utilities.runtime_state import get_primary_chat_id


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class MessageRequest(BaseModel):
    text: str = Field(
        default="Тестовое сообщение ✅",
        min_length=1,
        max_length=4096,
        description="Text that the bot will send to the primary chat.",
    )


def _authorize(api_key: str | None) -> None:
    if not BOT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BOT_API_KEY is not configured",
        )
    if not api_key or not secrets.compare_digest(api_key, BOT_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/messages")
async def send_message(
    payload: MessageRequest,
    x_api_key: str | None = Header(default=None),
) -> dict[str, str]:
    """Send a text notification to the chat last registered with /start or /test."""
    _authorize(x_api_key)
    chat_id = get_primary_chat_id()
    if not chat_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Primary chat is not configured. Send /start to the bot first.",
        )
    if not TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot token is not configured",
        )

    async with Bot(TOKEN) as bot:
        await bot.send_message(chat_id=chat_id, text=payload.text)
    return {"status": "sent"}
