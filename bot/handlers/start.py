from telegram import Update
from telegram.ext import CallbackContext


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Веб хук2. Это ТОЧНО новая версия! Которая ЗАДЕПЛОИЛАСЬ САМА! ПОЗДРАВЛЯЮЮЮЮЮЮЮ"
    )