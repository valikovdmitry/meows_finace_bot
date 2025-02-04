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
from bot.handlers.chat_id import show_chat_id
from bot.handlers.update import update
from bot.handlers.process import process_data
from bot.messages.conversation import handle_category, cancel


# Основная функция для запуска бота
def main(service, http_auth) -> None:
    # Создаём объект Application и передаем токен
    application = Application.builder().token(TOKEN).build()

    # Передаём service и http_auth в bot_data
    application.bot_data["service"] = service
    application.bot_data["http_auth"] = http_auth

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
    application.add_handler(CommandHandler("id", show_chat_id))
    application.add_handler(CommandHandler("update", update))
    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()