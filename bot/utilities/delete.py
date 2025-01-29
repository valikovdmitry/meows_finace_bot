from telegram import Update
from telegram.ext import CallbackContext


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