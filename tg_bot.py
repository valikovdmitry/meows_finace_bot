from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)
from find_category import find_args, find_category
from func_sheets import get_data_from_sheets, save_data_to_file
from write_data import write_to_first_empty_row
from load_from_env import token
import time
from prepare_reply import prepare_reply
from delete_last_row import clear_last_filled_row

# Состояния для ConversationHandler
WAITING_FOR_CATEGORY = 1


# Функция, которая будет вызываться при команде /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Хорошо, присылай свои данные 😊. Формат: Сумма, Категория, Описание"
    )


# Функция, которая будет вызываться при команде /update
async def update(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Обновляюсь!", parse_mode="HTML")
    data = get_data_from_sheets()
    save_data_to_file(data)
    await update.message.reply_text("Готовченко!", parse_mode="HTML")


# Функция, которая будет вызываться если текст == 'Удали' или 'удали'
async def delete_last_three_messages(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    last_message_id = update.message.message_id  # ID последнего сообщения

    deleted_count = 0  # Счетчик удаленных сообщений
    current_message_id = last_message_id  # Начинаем с одного меньше последнего

    while deleted_count < 3:  # Нам нужно удалить три сообщения
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=current_message_id)
            print(f"Сообщение с ID {current_message_id} было удалено.")
            deleted_count += 1
        except Exception as e:
            # Сообщение не найдено (например, оно уже удалено)
            print(f"Не удалось удалить сообщение с ID {current_message_id}: {e}")

        current_message_id -= 1  # Переходим к следующему сообщению


# Обработчик основного сообщения пользователя
async def process_data(update: Update, context: CallbackContext) -> int:
    # Запускаем таймер для оценки скорости работы
    start = time.time()

    # Получаем текст сообщения и выводим в терминал для отладки
    user_message = update.message.text  # Получаем текст от пользователя
    print(user_message)

    # Обработка данных на предмет текстовой команды
    if user_message.lower() == "удали":
        clear_last_filled_row()
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
        write_to_first_empty_row(m_sum, m_cat, m_desc)

        # Отправляем подтверждение и введенные данные
        reply_text = prepare_reply(m_sum, m_cat, m_desc)
        await update.message.reply_text(reply_text, parse_mode="HTML")

        # Останавливаем таймер и выводим время выполнения задачи
        end = time.time()
        elapsed_time = end - start
        print(f"Время выполнения: {elapsed_time:.2f} секунд")
        return ConversationHandler.END


# Обработчик ответа пользователя для уточнения категории
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
        write_to_first_empty_row(m_sum, m_cat, m_desc)

        # Подтверждаем запись и выводим введенные данные
        reply_text = prepare_reply(m_sum, m_cat, m_desc)
        await update.message.reply_text(reply_text, parse_mode="HTML")

        return ConversationHandler.END


# Обработчик для завершения разговора (на случай ошибки или отмены)
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Диалог отменен. 🛑")
    return ConversationHandler.END


# Основная функция для запуска бота
def main() -> None:
    # Создаём объект Application и передаем токен
    application = Application.builder().token(token).build()

    # Определяем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, process_data)],
        states={
            WAITING_FOR_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("update", update))
    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()