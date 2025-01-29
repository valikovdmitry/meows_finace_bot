from telegram import Update
from telegram.ext import CallbackContext

from config import SPREADSHEET_ID
from sheets.auth import get_service
from sheets.sheets_manager import get_categories
from utilities.file_manager import save_data_to_file


async def update(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Обновляюсь!", parse_mode="HTML")
    data = get_categories(get_service(), SPREADSHEET_ID)
    save_data_to_file(data)
    await update.message.reply_text("Готовченко!", parse_mode="HTML")


async def update_self() -> None:
    data = get_categories(get_service(), SPREADSHEET_ID)
    save_data_to_file(data)
    return