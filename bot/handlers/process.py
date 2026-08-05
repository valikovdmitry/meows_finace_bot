import time
import asyncio
from io import BytesIO

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import OPENAI_API_KEY, SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.keyboards import build_category_keyboard, get_categories_for_keyboard
from bot.utilities.delete import delete_last_three_messages
from bot.messages.conversation import send_success_message
from sheets.auth import get_service
from sheets.sheets_manager import delete_last_transaction, write_transaction
from utilities.category_memory import predict_category, learn_category
from utilities.text_process import find_amount_and_description
from utilities.voice_expense import parse_expense, transcribe_voice


def _delete_last_transaction_sync():
    service = get_service()
    delete_last_transaction(service, SPREADSHEET_ID)


def _write_transaction_sync(m_sum, m_cat, m_desc):
    service = get_service()
    write_transaction(m_sum, m_cat, m_desc, service)


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
    """Transcribe a Telegram voice message and save the extracted expense."""
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
        expense = await asyncio.to_thread(
            parse_expense,
            OPENAI_API_KEY,
            transcript,
            get_categories_for_keyboard(),
        )
    except Exception as exc:
        print(f"Не удалось обработать голосовое сообщение: {exc}")
        await status.edit_text("Не смог разобрать голосовое. Попробуй ещё раз или отправь трату текстом.")
        return ConversationHandler.END

    recognized_text = f"Распознано: {expense.transcript}"
    if expense.source_currency == "VND":
        recognized_text += f"\nКонвертация: {expense.source_amount} VND → {expense.amount_rub} ₽"
    await status.edit_text(recognized_text)
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
