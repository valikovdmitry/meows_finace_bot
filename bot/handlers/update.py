from telegram import Update
from telegram.ext import CallbackContext


async def update(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Обновляюсь!", parse_mode="HTML")
    data = get_categories()
    save_data_to_file(data)
    await update.message.reply_text("Готовченко!", parse_mode="HTML")