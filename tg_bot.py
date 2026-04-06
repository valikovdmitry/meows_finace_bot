from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    Defaults,
    MessageHandler,
    ConversationHandler,
    filters,
)
from zoneinfo import ZoneInfo

from config import TOKEN, BOT_TIMEZONE
from bot.states import WAITING_FOR_CATEGORY
from bot.handlers.start import start
from bot.handlers.update import update
from bot.handlers.shortcuts import quick_update, quick_test, quick_reminder_now
from bot.handlers.reminders import handle_reminder_reply, on_startup_schedule
from bot.handlers.reports import today_report, week_report, month_report, category_report
from bot.handlers.process import process_data
from bot.messages.conversation import (
    handle_category,
    handle_post_save_action,
    handle_category_button,
    cancel,
)





# Основная функция для запуска бота
def main() -> None:
    # Создаём объект Application и передаем токен
    application = (
        Application.builder()
        .token(TOKEN)
        .defaults(Defaults(tzinfo=ZoneInfo(BOT_TIMEZONE)))
        .post_init(on_startup_schedule)
        .build()
    )

    # Определяем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, process_data)],
        states={
            WAITING_FOR_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("update", update))
    application.add_handler(MessageHandler(filters.Regex("^Update$"), quick_update))
    application.add_handler(MessageHandler(filters.Regex("^Тест$"), quick_test))
    application.add_handler(MessageHandler(filters.Regex("^Дожим сейчас$"), quick_reminder_now))
    application.add_handler(MessageHandler(filters.Regex("^(Да|Нет|да|нет)$"), handle_reminder_reply))
    application.add_handler(CommandHandler("today", today_report))
    application.add_handler(CommandHandler("week", week_report))
    application.add_handler(CommandHandler("month", month_report))
    application.add_handler(CommandHandler("category", category_report))
    application.add_handler(CallbackQueryHandler(handle_post_save_action, pattern=r"^(undo_last|edit_last)$"))
    application.add_handler(CallbackQueryHandler(handle_category_button, pattern=r"^(catidx:\d+|cat_cancel|cat_show_all)$"))
    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()
