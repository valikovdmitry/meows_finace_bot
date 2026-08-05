import time
import asyncio
import uuid
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler

from config import OPENAI_API_KEY, SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.keyboards import build_category_keyboard, get_categories_for_keyboard
from bot.utilities.delete import delete_last_three_messages
from bot.messages.conversation import send_success_message
from sheets.auth import get_service
from sheets.sheets_manager import delete_last_transaction, write_transaction, write_transactions
from utilities.category_memory import predict_category, learn_category
from utilities.text_process import find_amount_and_description
from utilities.voice_expense import (
    VoiceExpense,
    group_expenses_by_category,
    parse_expenses,
    parse_receipt_image,
    transcribe_voice,
)


def _delete_last_transaction_sync():
    service = get_service()
    delete_last_transaction(service, SPREADSHEET_ID)


def _write_transaction_sync(m_sum, m_cat, m_desc):
    service = get_service()
    write_transaction(m_sum, m_cat, m_desc, service)


def _write_transactions_sync(transactions):
    service = get_service()
    write_transactions(transactions, service)


def _format_rubles(amount) -> str:
    value = float(amount)
    return f"{value:,.2f}".replace(",", " ").replace(".00", "")


def _batch_preview(expenses: list[VoiceExpense]) -> str:
    lines = [f"Нашёл {len(expenses)} трат:"]
    for expense in expenses:
        category = expense.category or "не распознана"
        lines.append(f"• {_format_rubles(expense.amount_rub)} ₽ — {category.strip(' -')} — {expense.description}")
    total = sum((expense.amount_rub for expense in expenses), start=0)
    lines.append(f"\nИтого: {_format_rubles(total)} ₽")
    return "\n".join(lines)


async def _request_batch_confirmation(
    update: Update,
    context: CallbackContext,
    expenses: list[VoiceExpense],
    source_message_id: int,
) -> int:
    unresolved = [expense.description for expense in expenses if not expense.category]
    if unresolved:
        await update.effective_chat.send_message(
            "Не смог определить категории для: " + ", ".join(unresolved) + ". Уточни их текстом."
        )
        return ConversationHandler.END

    batch_id = uuid.uuid4().hex[:12]
    context.user_data["pending_batch"] = {
        "id": batch_id,
        "transactions": [expense.transaction_fields() for expense in expenses],
        "source_message_id": source_message_id,
    }
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(f"Записать {len(expenses)}", callback_data=f"batch_save:{batch_id}"),
            InlineKeyboardButton("Отмена", callback_data=f"batch_cancel:{batch_id}"),
        ]]
    )
    await update.effective_chat.send_message(_batch_preview(expenses), reply_markup=keyboard)
    return ConversationHandler.END


async def handle_batch_action(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    action, _, batch_id = data.partition(":")
    pending = context.user_data.get("pending_batch")
    if not pending or pending.get("id") != batch_id:
        await query.edit_message_text("Этот пакет уже обработан или устарел.")
        return ConversationHandler.END

    if action == "batch_cancel":
        context.user_data.pop("pending_batch", None)
        await query.edit_message_text("Пакет не записан.")
        return ConversationHandler.END

    if action != "batch_save":
        return ConversationHandler.END

    transactions = pending["transactions"]
    context.user_data.pop("pending_batch", None)
    try:
        await asyncio.to_thread(_write_transactions_sync, transactions)
        for _amount, category, description in transactions:
            await asyncio.to_thread(learn_category, description, category)
    except Exception as exc:
        print(f"Не удалось записать пакет транзакций: {exc}")
        context.user_data["pending_batch"] = pending
        await query.edit_message_text("Не удалось записать пакет. Нажми «Записать» ещё раз.")
        return ConversationHandler.END

    await query.edit_message_text(f"Записано строк: {len(transactions)}.")
    return ConversationHandler.END


async def process_transaction_text(
    update: Update,
    context: CallbackContext,
    user_message: str,
    source_message_id: int | None = None,
) -> int:
    start = time.time()
    # Обработка данных на предмет текстовой команды
    if user_message.lower() == "удали":
        await asyncio.to_thread(_delete_last_transaction_sync)
        await delete_last_three_messages(update, context)
        return ConversationHandler.END

    # Проверяем сообщение на удовлетворение условий бота
    if len(user_message.split()) < 2 or not any(char.isdigit() for char in user_message):
        print("Сообщение игнорировано (некорректный формат).")
        return  # Просто выходим из функции

    # Всегда сначала берем сумму и описание, а категорию выбираем отдельным шагом.
    m_sum, m_desc = find_amount_and_description(user_message)
    if not m_sum:
        await update.effective_chat.send_message("Не смог распознать сумму. Пример: 150 кофе")
        return ConversationHandler.END

    if not m_desc:
        await update.effective_chat.send_message("Добавь описание после суммы. Пример: 150 кофе")
        return ConversationHandler.END

    if source_message_id is None and update.message:
        source_message_id = update.message.message_id

    predicted_category = await asyncio.to_thread(predict_category, m_desc)
    if predicted_category:
        await asyncio.to_thread(_write_transaction_sync, m_sum, predicted_category, m_desc)
        await asyncio.to_thread(learn_category, m_desc, predicted_category)
        elapsed_time = time.time() - start
        await send_success_message(
            update,
            context,
            m_sum,
            predicted_category,
            m_desc,
            elapsed_time,
            source_message_id=source_message_id,
        )
        return ConversationHandler.END

    prompt_message = await update.effective_chat.send_message(
        "Выбери категорию:",
        reply_markup=build_category_keyboard(),
    )
    context.user_data["pending_tx"] = {
        "m_sum": m_sum,
        "m_desc": m_desc,
        "memory_desc": m_desc,
        "source_message_id": source_message_id,
        "prompt_message_id": prompt_message.message_id,
    }
    context.user_data["start_time"] = start
    return WAITING_FOR_CATEGORY


async def process_data(update: Update, context: CallbackContext) -> int:
    user_message = update.message.text
    print(user_message)
    return await process_transaction_text(update, context, user_message)


async def process_voice_data(update: Update, context: CallbackContext) -> int:
    """Transcribe a voice message and save one expense or confirm a batch."""
    start = time.time()
    if not OPENAI_API_KEY:
        await update.effective_chat.send_message(
            "Голосовые траты пока не настроены: добавь OPENAI_API_KEY в .env и перезапусти бота."
        )
        return ConversationHandler.END

    message = update.message
    if message is None or message.voice is None:
        return ConversationHandler.END

    status = await update.effective_chat.send_message("Распознаю голосовое сообщение…")
    try:
        telegram_file = await context.bot.get_file(message.voice.file_id)
        audio = BytesIO()
        await telegram_file.download_to_memory(out=audio)
        transcript = await asyncio.to_thread(
            transcribe_voice,
            OPENAI_API_KEY,
            audio.getvalue(),
            "voice.ogg",
        )
        expenses = await asyncio.to_thread(
            parse_expenses,
            OPENAI_API_KEY,
            transcript,
            get_categories_for_keyboard(),
        )
        expenses = group_expenses_by_category(expenses)
    except Exception as exc:
        print(f"Не удалось обработать голосовое сообщение: {exc}")
        await status.edit_text("Не смог разобрать голосовое. Попробуй ещё раз или отправь трату текстом.")
        return ConversationHandler.END

    recognized_text = f"Распознано: {transcript}"
    conversions = [
        f"{expense.source_amount} VND → {expense.amount_rub} ₽"
        for expense in expenses
        if expense.source_currency == "VND"
    ]
    if conversions:
        recognized_text += "\nКонвертация: " + "; ".join(conversions)
    await status.edit_text(recognized_text)

    if len(expenses) > 1:
        return await _request_batch_confirmation(update, context, expenses, message.message_id)

    expense = expenses[0]
    if expense.category:
        amount, category, description = expense.transaction_fields()
        await asyncio.to_thread(_write_transaction_sync, amount, category, description)
        await asyncio.to_thread(learn_category, description, category)
        await send_success_message(
            update,
            context,
            amount,
            category,
            description,
            time.time() - start,
            source_message_id=message.message_id,
        )
        return ConversationHandler.END

    amount = float(expense.amount_rub)
    prompt_message = await update.effective_chat.send_message(
        "Не смог уверенно выбрать категорию. Выбери её:",
        reply_markup=build_category_keyboard(),
    )
    context.user_data["pending_tx"] = {
        "m_sum": amount,
        "m_desc": expense.description,
        "memory_desc": expense.description,
        "source_message_id": message.message_id,
        "prompt_message_id": prompt_message.message_id,
    }
    context.user_data["start_time"] = time.time()
    return WAITING_FOR_CATEGORY


async def process_photo_data(update: Update, context: CallbackContext) -> int:
    """Read a receipt image, then offer a confirmed batch of transactions."""
    if not OPENAI_API_KEY:
        await update.effective_chat.send_message(
            "Фото чеков пока не настроены: добавь OPENAI_API_KEY в .env и перезапусти бота."
        )
        return ConversationHandler.END

    message = update.message
    if message is None or not message.photo:
        return ConversationHandler.END

    status = await update.effective_chat.send_message("Читаю чек…")
    try:
        telegram_file = await context.bot.get_file(message.photo[-1].file_id)
        image = BytesIO()
        await telegram_file.download_to_memory(out=image)
        expenses = await asyncio.to_thread(
            parse_receipt_image,
            OPENAI_API_KEY,
            image.getvalue(),
            "image/jpeg",
            get_categories_for_keyboard(),
        )
        expenses = group_expenses_by_category(expenses)
    except Exception as exc:
        print(f"Не удалось обработать фото чека: {exc}")
        await status.edit_text("Не смог прочитать чек. Попробуй фото крупнее и без бликов.")
        return ConversationHandler.END

    await status.edit_text("Чек распознан. Проверь строки перед сохранением.")
    return await _request_batch_confirmation(update, context, expenses, message.message_id)
