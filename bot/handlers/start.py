from telegram import Update
from telegram.ext import CallbackContext

from bot.handlers.reminders import remember_chat
from bot.utilities.keyboards import build_main_keyboard


async def start(update: Update, context: CallbackContext) -> None:
    if update.effective_chat:
        remember_chat(update.effective_chat.id)
    await update.message.reply_text(
        "Бот запущен. Отправь сумму и описание, например: 150 такси",
        reply_markup=build_main_keyboard(),
    )
