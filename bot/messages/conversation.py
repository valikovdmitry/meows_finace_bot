import asyncio
import time

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.states import WAITING_FOR_CATEGORY
from sheets.auth import get_service
from sheets.sheets_manager import write_transaction
from utilities.text_process import find_category
from utilities.reply_manager import format_reply


def _write_transaction_sync(m_sum, m_cat, m_desc):
    service = get_service()
    write_transaction(m_sum, m_cat, m_desc, service)


async def handle_category(update: Update, context: CallbackContext) -> int:
    message = update.message.text  # Получаем новую категорию от пользователя
    m_cat = find_category(message)
    m_sum = context.user_data["m_sum"]
    m_desc = context.user_data["m_desc"]
    start_time = context.user_data.get("start_time")
    if m_cat == '- Нераспознанное':
        await update.message.reply_text(
            f"Хозяин, не вижу категорию, уточни! 🥺 "
        )
        # Сохраняем данные в context для последующей обработки
        context.user_data["m_sum"] = m_sum
        context.user_data["m_desc"] = m_desc
        return WAITING_FOR_CATEGORY
    else:
        # Записываем данные в таблицу с обновленной категорией
        await asyncio.to_thread(_write_transaction_sync, m_sum, m_cat, m_desc)

        # Подтверждаем запись и выводим введенные данные
        elapsed_time = None
        if start_time is not None:
            elapsed_time = time.time() - start_time
        reply_text = format_reply(m_sum, m_cat, m_desc, elapsed_time)
        await update.effective_chat.send_message(reply_text, parse_mode="HTML")
        context.user_data.pop("start_time", None)

        return ConversationHandler.END

# Обработчик для завершения разговора (на случай ошибки или отмены)
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Диалог отменен. 🛑")
    return ConversationHandler.END
