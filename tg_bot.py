from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import TOKEN
from bot.states import WAITING_FOR_CATEGORY
from bot.handlers.start import start
from bot.handlers.update import update
from bot.handlers.process import process_data
from bot.messages.conversation import handle_category, cancel





# Основная функция для запуска бота
def main() -> None:
    # Создаём объект Application и передаем токен
    application = Application.builder().token(TOKEN).build()

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