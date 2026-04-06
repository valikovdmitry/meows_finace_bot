import time
import asyncio

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.keyboards import build_category_keyboard
from bot.utilities.delete import delete_last_three_messages
from bot.messages.conversation import send_success_message
from sheets.auth import get_service
from sheets.sheets_manager import delete_last_transaction, write_transaction
from utilities.text_process import find_args


def _delete_last_transaction_sync():
    service = get_service()
    delete_last_transaction(service, SPREADSHEET_ID)


def _write_transaction_sync(m_sum, m_cat, m_desc):
    service = get_service()
    write_transaction(m_sum, m_cat, m_desc, service)


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

    # Делаем анализ и получаем сумму, категорию и описание
    m_sum, m_cat, m_desc = find_args(user_message)

    if m_cat == "- Нераспознанное":
        await update.effective_chat.send_message(
            "Хозяин, не вижу категорию, уточни! 🥺",
            reply_markup=build_category_keyboard(),
        )
        # Сохраняем данные в context для последующей обработки
        context.user_data["pending_tx"] = {"m_sum": m_sum, "m_desc": m_desc}
        context.user_data["start_time"] = start
        return WAITING_FOR_CATEGORY
    else:
        # Записываем данные в таблицу
        await asyncio.to_thread(_write_transaction_sync, m_sum, m_cat, m_desc)

        elapsed_time = time.time() - start
        # Отправляем подтверждение и введенные данные
        await send_success_message(update, context, m_sum, m_cat, m_desc, elapsed_time)

        # Выводим время выполнения задачи
        print(f"Время выполнения: {elapsed_time:.2f} секунд")

        return ConversationHandler.END
