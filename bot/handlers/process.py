import gc
import time
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.delete import delete_last_three_messages
from sheets.sheets_manager import delete_last_transaction, write_transaction
from utilities.text_process import find_args
from utilities.reply_manager import format_reply


async def process_data(update: Update, context: CallbackContext) -> int:
    service = context.bot_data.get("service")
    http_auth = context.bot_data.get("http_auth")
    start = time.time()
    user_message = update.message.text
    print(f"\n{user_message}")

    if user_message.lower() == "удали":
        delete_last_transaction(service, http_auth, SPREADSHEET_ID)
        await delete_last_three_messages(update, context)
        return ConversationHandler.END

    if len(user_message.split()) < 2 or not any(char.isdigit() for char in user_message):
        print("Сообщение игнорировано (некорректный формат).")
        return

    # Делаем анализ и получаем сумму, категорию и описание
    m_sum, m_cat, m_desc = find_args(user_message)

    if m_cat == "- Нераспознанное":
        await update.message.reply_text(f"Хозяин, не вижу категорию, уточни! 🥺 ")
        context.user_data["m_sum"] = m_sum
        context.user_data["m_desc"] = m_desc
        return WAITING_FOR_CATEGORY
    else:
        write_transaction(m_sum, m_cat, m_desc, service, http_auth)
        reply_text = format_reply(m_sum, m_cat, m_desc)
        await update.message.reply_text(reply_text, parse_mode="HTML")

        end = time.time()
        elapsed_time = end - start
        print(f"Время выполнения: {elapsed_time:.2f} секунд")

        http_auth.close()
        gc.collect()

        return ConversationHandler.END