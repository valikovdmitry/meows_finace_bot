from telegram import Update
from telegram.ext import CallbackContext

from bot.handlers.update import update
from bot.handlers.process import process_transaction_text
from bot.handlers.reminders import trigger_reminder_now


async def quick_update(update_obj: Update, context: CallbackContext) -> None:
    await update(update_obj, context)


async def quick_test(update_obj: Update, context: CallbackContext) -> None:
    test_text = "100 кофе"
    sent = await update_obj.effective_chat.send_message(test_text)
    await process_transaction_text(update_obj, context, test_text, source_message_id=sent.message_id)


async def quick_reminder_now(update_obj: Update, context: CallbackContext) -> None:
    if not update_obj.effective_chat:
        return
    await trigger_reminder_now(context.application, update_obj.effective_chat.id)
