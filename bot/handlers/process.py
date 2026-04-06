import time
import asyncio

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.keyboards import build_category_keyboard
from bot.utilities.delete import delete_last_three_messages
from sheets.auth import get_service
from sheets.sheets_manager import delete_last_transaction
from utilities.text_process import find_amount_and_description


def _delete_last_transaction_sync():
    service = get_service()
    delete_last_transaction(service, SPREADSHEET_ID)


async def process_data(update: Update, context: CallbackContext) -> int:
    # Запускаем таймер для оценки скорости работы
    start = time.time()

    # Получаем текст сообщения и выводим в терминал для отладки
    user_message = update.message.text  # Получаем текст от пользователя
    print(user_message)

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

    await update.effective_chat.send_message(
        "Выбери категорию:",
        reply_markup=build_category_keyboard(),
    )
    context.user_data["pending_tx"] = {"m_sum": m_sum, "m_desc": m_desc}
    context.user_data["start_time"] = start
    return WAITING_FOR_CATEGORY
