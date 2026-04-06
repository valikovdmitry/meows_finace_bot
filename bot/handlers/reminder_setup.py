import datetime as dt
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.handlers.custom_reminders import (
    FREQUENCY_LABELS,
    LABEL_TO_FREQUENCY,
    delete_scheduled_reminder,
    schedule_reminder,
)
from config import BOT_TIMEZONE
from utilities.reminders_store import delete_reminder, get_reminder, list_reminders, upsert_reminder


ASK_TEXT, ASK_DATE, ASK_TIME, ASK_FREQUENCY = range(100, 104)


def _fmt_reminder(item: dict):
    freq = FREQUENCY_LABELS.get(item.get("frequency"), item.get("frequency", ""))
    start = dt.datetime.fromisoformat(item["start_at"])
    start_local = start.astimezone(ZoneInfo(BOT_TIMEZONE))
    return (
        f"#{item['id']}\n"
        f"Сообщение: {item['text']}\n"
        f"Старт: {start_local.strftime('%Y-%m-%d %H:%M')}\n"
        f"Частота: {freq}"
    )


def _freq_keyboard():
    labels = list(FREQUENCY_LABELS.values())
    rows = []
    for i in range(0, len(labels), 2):
        rows.append(labels[i : i + 2])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def remind_start(update: Update, context: CallbackContext) -> int:
    context.user_data["remind_form"] = {"mode": "create"}
    await update.effective_chat.send_message("Какое сообщение нужно присылать?")
    return ASK_TEXT


async def reminders_list(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return
    items = [x for x in list_reminders() if x.get("chat_id") == chat_id]
    if not items:
        await update.effective_chat.send_message("Список напоминаний пуст. Создай через /remind")
        return

    for item in items:
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Изменить", callback_data=f"reminder_edit:{item['id']}"),
                    InlineKeyboardButton("Удалить", callback_data=f"reminder_delete:{item['id']}"),
                ]
            ]
        )
        await update.effective_chat.send_message(_fmt_reminder(item), reply_markup=kb)


async def reminder_edit_start(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    reminder_id = (query.data or "").split(":", 1)[1]
    item = get_reminder(reminder_id)
    if not item:
        await query.edit_message_text("Напоминание не найдено.")
        return ConversationHandler.END

    context.user_data["remind_form"] = {"mode": "edit", "id": reminder_id, "original": item}
    await query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message(
        f"Редактируем #{reminder_id}\n"
        f"Текущее сообщение: {item['text']}\n"
        "Отправь новое сообщение или `.` чтобы оставить текущее."
    )
    return ASK_TEXT


async def reminder_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    reminder_id = (query.data or "").split(":", 1)[1]
    removed = delete_reminder(reminder_id)
    delete_scheduled_reminder(context.application, reminder_id)
    await query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message("Удалено." if removed else "Не найдено.")


async def remind_set_text(update: Update, context: CallbackContext) -> int:
    form = context.user_data.get("remind_form", {})
    text = (update.message.text or "").strip()
    if not text:
        await update.effective_chat.send_message("Сообщение не может быть пустым.")
        return ASK_TEXT
    if text == "." and form.get("mode") == "edit":
        text = form.get("original", {}).get("text", "")
    form["text"] = text
    context.user_data["remind_form"] = form

    default_date = dt.datetime.now(ZoneInfo(BOT_TIMEZONE)).strftime("%Y-%m-%d")
    if form.get("mode") == "edit":
        default_date = dt.datetime.fromisoformat(form["original"]["start_at"]).astimezone(ZoneInfo(BOT_TIMEZONE)).strftime("%Y-%m-%d")
    await update.effective_chat.send_message(
        f"С какой даты начать? Формат YYYY-MM-DD\nТекущая: {default_date}\nОтправь `.` чтобы оставить."
    )
    return ASK_DATE


async def remind_set_date(update: Update, context: CallbackContext) -> int:
    form = context.user_data.get("remind_form", {})
    value = (update.message.text or "").strip()
    if value == "." and form.get("mode") == "edit":
        value = dt.datetime.fromisoformat(form["original"]["start_at"]).astimezone(ZoneInfo(BOT_TIMEZONE)).strftime("%Y-%m-%d")
    try:
        dt.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        await update.effective_chat.send_message("Неверная дата. Пример: 2026-04-06")
        return ASK_DATE
    form["date"] = value
    context.user_data["remind_form"] = form

    default_time = "10:00"
    if form.get("mode") == "edit":
        default_time = dt.datetime.fromisoformat(form["original"]["start_at"]).astimezone(ZoneInfo(BOT_TIMEZONE)).strftime("%H:%M")
    await update.effective_chat.send_message(
        f"В какое время присылать? Формат HH:MM\nТекущее: {default_time}\nОтправь `.` чтобы оставить."
    )
    return ASK_TIME


async def remind_set_time(update: Update, context: CallbackContext) -> int:
    form = context.user_data.get("remind_form", {})
    value = (update.message.text or "").strip()
    if value == "." and form.get("mode") == "edit":
        value = dt.datetime.fromisoformat(form["original"]["start_at"]).astimezone(ZoneInfo(BOT_TIMEZONE)).strftime("%H:%M")
    try:
        dt.datetime.strptime(value, "%H:%M")
    except ValueError:
        await update.effective_chat.send_message("Неверное время. Пример: 16:30")
        return ASK_TIME
    form["time"] = value
    context.user_data["remind_form"] = form
    await update.effective_chat.send_message(
        "Как часто присылать?",
        reply_markup=_freq_keyboard(),
    )
    return ASK_FREQUENCY


async def remind_set_frequency(update: Update, context: CallbackContext) -> int:
    form = context.user_data.get("remind_form", {})
    value = (update.message.text or "").strip()

    if value == "." and form.get("mode") == "edit":
        freq_key = form["original"]["frequency"]
    else:
        freq_key = LABEL_TO_FREQUENCY.get(value)
    if not freq_key:
        await update.effective_chat.send_message("Выбери частоту кнопкой.", reply_markup=_freq_keyboard())
        return ASK_FREQUENCY

    tz = ZoneInfo(BOT_TIMEZONE)
    start_at = dt.datetime.strptime(f"{form['date']} {form['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    reminder = {
        "id": form.get("id"),
        "chat_id": update.effective_chat.id,
        "text": form["text"],
        "start_at": start_at.isoformat(),
        "frequency": freq_key,
        "active": True,
    }
    reminder = upsert_reminder(reminder)
    schedule_reminder(context.application, reminder)

    await update.effective_chat.send_message(
        "Готово, напоминание сохранено:\n" + _fmt_reminder(reminder),
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.pop("remind_form", None)
    return ConversationHandler.END


async def remind_cancel(update: Update, context: CallbackContext) -> int:
    context.user_data.pop("remind_form", None)
    await update.effective_chat.send_message("Окей, отменил настройку напоминания.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
