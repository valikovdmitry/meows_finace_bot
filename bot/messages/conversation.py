from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.states import WAITING_FOR_CATEGORY
from sheets.auth import get_service
from sheets.sheets_manager import write_transaction
from utilities.text_process import find_category
from utilities.reply_manager import format_reply


async def handle_category(update: Update, context: CallbackContext) -> int:
    message = update.message.text  # Получаем новую категорию от пользователя
    m_cat = find_category(message)
    m_sum = context.user_data["m_sum"]
    m_desc = context.user_data["m_desc"]
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
        write_transaction(m_sum, m_cat, m_desc, get_service([0]))
        http_auth = get_service([1])
        http_auth.close()

        # Подтверждаем запись и выводим введенные данные
        reply_text = format_reply(m_sum, m_cat, m_desc)
        await update.message.reply_text(reply_text, parse_mode="HTML")

        return ConversationHandler.END

# Обработчик для завершения разговора (на случай ошибки или отмены)
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Диалог отменен. 🛑")
    return ConversationHandler.END