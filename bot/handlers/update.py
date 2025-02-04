from telegram import Update
from telegram.ext import CallbackContext
import gc

from config import SPREADSHEET_ID
from sheets.sheets_manager import load_categories
from utilities.file_manager import save_data_to_file, load_data_from_file
from utilities.memory_manager import get_memory_usage


async def update(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Обновляюсь!", parse_mode="HTML")

    service = context.bot_data.get("service")
    http_auth = context.bot_data.get("http_auth")

    data = load_categories(service, http_auth, SPREADSHEET_ID)
    save_data_to_file(data)

    http_auth.close()
    gc.collect()

    await update.message.reply_text("Готовченко!", parse_mode="HTML")


def update_self(service, http_auth) -> None:
    data = load_data_from_file()
    if data == {}:
        data = load_categories(service, http_auth, SPREADSHEET_ID)
        save_data_to_file(data)

        http_auth.close()
        gc.collect()

        print('---------- после update_self ----------')
        get_memory_usage()
        return
    else:
        return