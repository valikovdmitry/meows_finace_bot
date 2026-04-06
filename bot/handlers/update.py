import asyncio

from telegram import Update
from telegram.ext import CallbackContext

from config import SPREADSHEET_ID
from sheets.auth import get_service
from sheets.sheets_manager import get_categories
from utilities.file_manager import save_data_to_file


def _fetch_categories_sync():
    service = get_service()
    return get_categories(service, SPREADSHEET_ID)


async def update(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Обновляюсь!", parse_mode="HTML")
    data = await asyncio.to_thread(_fetch_categories_sync)

    await asyncio.to_thread(save_data_to_file, data)
    await update.message.reply_text("Готовченко!", parse_mode="HTML")


def update_self() -> None:
    data = _fetch_categories_sync()

    save_data_to_file(data)
    return
