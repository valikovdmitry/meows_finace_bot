import time

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import SPREADSHEET_ID
from bot.states import WAITING_FOR_CATEGORY
from bot.utilities.delete import delete_last_three_messages
from sheets.auth import get_service
from sheets.sheets_manager import delete_last_transaction, write_transaction
from utilities.text_process import find_args
from utilities.reply_manager import format_reply

async def process_data(update: Update, context: CallbackContext) -> int:
    # Запускаем таймер для оценки скорости работы
    start = time.time()

    # Получаем текст сообщения и выводим в терминал для отладки
    user_message = update.message.text  # Получаем текст от пользователя
    print(user_message)

    # Обработка данных на предмет текстовой команды
    if user_message.lower() == "удали":
        service, http_auth = get_service()
        try:
            delete_last_transaction(service, SPREADSHEET_ID)
        finally:
            http_auth.close()
        await delete_last_three_messages(update, context)
        return ConversationHandler.END

    # Проверяем сообщение на удовлетворение условий бота
    if len(user_message.split()) < 2 or not any(char.isdigit() for char in user_message):
        print("Сообщение игнорировано (некорректный формат).")
        return  # Просто выходим из функции

    # Делаем анализ и получаем сумму, категорию и описание
    m_sum, m_cat, m_desc = find_args(user_message)

    if m_cat == "- Нераспознанное":
        await update.message.reply_text(
            f"Хозяин, не вижу категорию, уточни! 🥺 "
        )
        # Сохраняем данные в context для последующей обработки
        context.user_data["m_sum"] = m_sum
        context.user_data["m_desc"] = m_desc
        return WAITING_FOR_CATEGORY
    else:
        # Записываем данные в таблицу
        service, http_auth = get_service()
        try:
            write_transaction(m_sum, m_cat, m_desc, service)
        finally:
            http_auth.close()

        # Отправляем подтверждение и введенные данные
        reply_text = format_reply(m_sum, m_cat, m_desc)
        await update.message.reply_text(reply_text, parse_mode="HTML")

        # Останавливаем таймер и выводим время выполнения задачи
        end = time.time()
        elapsed_time = end - start
        print(f"Время выполнения: {elapsed_time:.2f} секунд")

        return ConversationHandler.END
