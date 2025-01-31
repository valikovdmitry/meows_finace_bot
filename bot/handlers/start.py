from telegram import Update
from telegram.ext import CallbackContext


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Webhook test 4. Если все прошло успешно, поздравляю! Вебхук настроен!"
    )