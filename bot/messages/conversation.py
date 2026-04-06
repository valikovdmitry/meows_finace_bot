import asyncio
import time

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.keyboards import (
    build_category_keyboard,
    build_post_save_keyboard,
    get_categories_for_keyboard,
)
from sheets.auth import get_service
from sheets.sheets_manager import delete_last_transaction, write_transaction
from utilities.text_process import find_category
from utilities.reply_manager import format_reply


def _write_transaction_sync(m_sum, m_cat, m_desc):
    service = get_service()
    write_transaction(m_sum, m_cat, m_desc, service)


def _delete_last_transaction_sync():
    service = get_service()
    delete_last_transaction(service, SPREADSHEET_ID)


async def send_success_message(update: Update, context: CallbackContext, m_sum, m_cat, m_desc, elapsed_time):
    reply_text = format_reply(m_sum, m_cat, m_desc, elapsed_time)
    await update.effective_chat.send_message(
        reply_text,
        parse_mode="HTML",
        reply_markup=build_post_save_keyboard(),
    )
    context.user_data["last_tx"] = {"m_sum": m_sum, "m_cat": m_cat, "m_desc": m_desc}


def _pending_tx(context: CallbackContext):
    if "pending_tx" in context.user_data:
        return context.user_data["pending_tx"]

    m_sum = context.user_data.get("m_sum")
    m_desc = context.user_data.get("m_desc")
    if m_sum is None:
        return None

    return {"m_sum": m_sum, "m_desc": m_desc}


async def handle_category(update: Update, context: CallbackContext) -> int:
    message = update.message.text  # Получаем новую категорию от пользователя
    m_cat = find_category(message)
    pending = _pending_tx(context)
    if not pending:
        await update.effective_chat.send_message("Нет ожидающей транзакции. Отправь сумму и описание заново.")
        return ConversationHandler.END
    m_sum = pending["m_sum"]
    m_desc = pending["m_desc"]
    start_time = context.user_data.get("start_time")
    if m_cat == '- Нераспознанное':
        await update.effective_chat.send_message(
            "Хозяин, не вижу категорию, уточни! 🥺",
            reply_markup=build_category_keyboard(),
        )
        context.user_data["pending_tx"] = {"m_sum": m_sum, "m_desc": m_desc}
        return WAITING_FOR_CATEGORY
    else:
        # Записываем данные в таблицу с обновленной категорией
        await asyncio.to_thread(_write_transaction_sync, m_sum, m_cat, m_desc)

        # Подтверждаем запись и выводим введенные данные
        elapsed_time = None
        if start_time is not None:
            elapsed_time = time.time() - start_time
        await send_success_message(update, context, m_sum, m_cat, m_desc, elapsed_time)
        context.user_data.pop("pending_tx", None)
        context.user_data.pop("start_time", None)

        return ConversationHandler.END


async def handle_category_button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    pending = _pending_tx(context)
    if not pending:
        await query.edit_message_text("Нет ожидающей транзакции. Отправь сумму и описание заново.")
        return ConversationHandler.END

    categories = get_categories_for_keyboard()
    data = query.data or ""
    if data == "cat_cancel":
        context.user_data.pop("pending_tx", None)
        context.user_data.pop("start_time", None)
        await query.edit_message_text("Окей, отменил выбор категории.")
        return ConversationHandler.END

    if not data.startswith("catidx:"):
        return WAITING_FOR_CATEGORY
    try:
        idx = int(data.split(":", 1)[1])
        m_cat = categories[idx]
    except (ValueError, IndexError):
        await query.edit_message_text("Категория устарела, отправь сумму заново.")
        return ConversationHandler.END

    m_sum = pending["m_sum"]
    m_desc = pending["m_desc"]
    await asyncio.to_thread(_write_transaction_sync, m_sum, m_cat, m_desc)

    start_time = context.user_data.get("start_time")
    elapsed_time = None
    if start_time is not None:
        elapsed_time = time.time() - start_time

    await query.edit_message_text("Категория выбрана, записываю.")
    await send_success_message(update, context, m_sum, m_cat, m_desc, elapsed_time)
    context.user_data.pop("pending_tx", None)
    context.user_data.pop("start_time", None)
    return ConversationHandler.END


async def handle_post_save_action(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data or ""

    if action == "undo_last":
        await asyncio.to_thread(_delete_last_transaction_sync)
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message("Последнюю транзакцию удалил.")
        return ConversationHandler.END

    if action == "edit_last":
        last_tx = context.user_data.get("last_tx")
        if not last_tx:
            await update.effective_chat.send_message("Не нашел последнюю транзакцию для редактирования.")
            return ConversationHandler.END

        await asyncio.to_thread(_delete_last_transaction_sync)
        context.user_data["pending_tx"] = {"m_sum": last_tx["m_sum"], "m_desc": last_tx["m_desc"]}
        context.user_data["start_time"] = time.time()
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(
            "Удалил последнюю запись. Выбери новую категорию:",
            reply_markup=build_category_keyboard(),
        )
        return WAITING_FOR_CATEGORY

    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    context.user_data.pop("pending_tx", None)
    context.user_data.pop("start_time", None)
    await update.message.reply_text("Диалог отменен. 🛑")
    return ConversationHandler.END
