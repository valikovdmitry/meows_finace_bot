from telegram import Update
from telegram.ext import CallbackContext


async def show_chat_id(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Ваш Chat ID: {chat_id}")