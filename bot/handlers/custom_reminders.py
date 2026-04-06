import datetime as dt
from zoneinfo import ZoneInfo

from telegram.ext import Application, CallbackContext

from config import BOT_TIMEZONE
from utilities.reminders_store import list_reminders


FREQUENCY_TO_DELTA = {
    "5m": dt.timedelta(minutes=5),
    "15m": dt.timedelta(minutes=15),
    "30m": dt.timedelta(minutes=30),
    "1h": dt.timedelta(hours=1),
    "3h": dt.timedelta(hours=3),
    "6h": dt.timedelta(hours=6),
    "12h": dt.timedelta(hours=12),
    "1d": dt.timedelta(days=1),
    "3d": dt.timedelta(days=3),
    "1w": dt.timedelta(weeks=1),
    "2w": dt.timedelta(weeks=2),
    "1mo": dt.timedelta(days=30),
}

FREQUENCY_LABELS = {
    "5m": "Каждые 5 минут",
    "15m": "Каждые 15 минут",
    "30m": "Каждые 30 минут",
    "1h": "Каждый 1 час",
    "3h": "Каждые 3 часа",
    "6h": "Каждые 6 часов",
    "12h": "Каждые 12 часов",
    "1d": "Раз в день",
    "3d": "Раз в 3 дня",
    "1w": "Раз в неделю",
    "2w": "Раз в 2 недели",
    "1mo": "Раз в месяц (30 дней)",
}

LABEL_TO_FREQUENCY = {v: k for k, v in FREQUENCY_LABELS.items()}


def _job_name(reminder_id: str):
    return f"custom_reminder_{reminder_id}"


def _parse_iso(value: str):
    return dt.datetime.fromisoformat(value)


async def _send_custom_reminder(context: CallbackContext):
    reminder = context.job.data.get("reminder", {})
    chat_id = reminder.get("chat_id")
    text = reminder.get("text")
    if not chat_id or not text:
        return
    await context.bot.send_message(chat_id=chat_id, text=text)


def _unschedule(app: Application, reminder_id: str):
    jq = app.job_queue
    if jq is None:
        return
    for job in jq.get_jobs_by_name(_job_name(reminder_id)):
        job.schedule_removal()


def schedule_reminder(app: Application, reminder: dict):
    jq = app.job_queue
    if jq is None:
        return
    reminder_id = reminder.get("id")
    if not reminder_id:
        return

    _unschedule(app, reminder_id)

    freq = reminder.get("frequency")
    delta = FREQUENCY_TO_DELTA.get(freq)
    if delta is None:
        return

    tz = ZoneInfo(BOT_TIMEZONE)
    start_at = _parse_iso(reminder["start_at"])
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=tz)
    now = dt.datetime.now(tz)

    first = start_at
    while first <= now:
        first += delta

    jq.run_repeating(
        _send_custom_reminder,
        interval=delta,
        first=first,
        data={"reminder": reminder},
        name=_job_name(reminder_id),
    )


def delete_scheduled_reminder(app: Application, reminder_id: str):
    _unschedule(app, reminder_id)


def schedule_all_custom_reminders(app: Application):
    jq = app.job_queue
    if jq is None:
        return
    for reminder in list_reminders():
        if not reminder.get("active", True):
            continue
        schedule_reminder(app, reminder)
