from telegram import Update
from telegram.ext import CallbackContext


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Хорошо, присылай свои данные 😊. Формат: Сумма, Категория, Описание"
    )