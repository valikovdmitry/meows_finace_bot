import datetime as dt
from zoneinfo import ZoneInfo

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext

from bot.utilities.keyboards import build_main_keyboard
from bot.handlers.custom_reminders import schedule_all_custom_reminders
from config import BOT_TIMEZONE
from utilities.runtime_state import get_primary_chat_id, set_primary_chat_id


REMINDER_PROMPT = (
    "Есть ли у вас траты, которые вы сегодня не записали?\n"
    "Если есть, лучше внести сейчас — потом будет сложнее вспоминать."
)
YES_FOLLOWUP = "Запишите лучше сейчас, потом действительно сложнее вспоминать."
NO_FOLLOWUP = "Молодцы, это точно поможет в будущем. Так держать."
REMINDER_KB = ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True, one_time_keyboard=True)


def _job_queue(app: Application):
    return app.job_queue


def _state(app: Application):
    return app.bot_data.setdefault(
        "reminder_state",
        {
            "active": False,
            "chat_id": None,
            "question_message_id": None,
            "daily_registered": False,
        },
    )


async def _safe_delete_by_id(bot, chat_id: int, message_id: int | None):
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def _send_question(app: Application, chat_id: int):
    state = _state(app)
    await _safe_delete_by_id(app.bot, chat_id, state.get("question_message_id"))
    sent = await app.bot.send_message(chat_id=chat_id, text=REMINDER_PROMPT, reply_markup=REMINDER_KB)
    state["question_message_id"] = sent.message_id
    state["chat_id"] = chat_id


def _cancel_followups(app: Application, chat_id: int):
    jq = _job_queue(app)
    if jq is None:
        return
    for job in jq.get_jobs_by_name(f"reminder_followup_{chat_id}"):
        job.schedule_removal()


async def _start_cycle(app: Application, chat_id: int):
    state = _state(app)
    if state.get("active") and state.get("chat_id") == chat_id:
        return
    state["active"] = True
    state["chat_id"] = chat_id
    await _send_question(app, chat_id)
    jq = _job_queue(app)
    if jq is None:
        return
    _cancel_followups(app, chat_id)
    jq.run_repeating(
        _followup_job,
        interval=dt.timedelta(minutes=15),
        first=dt.timedelta(minutes=15),
        data={"chat_id": chat_id},
        name=f"reminder_followup_{chat_id}",
    )


async def _stop_cycle(app: Application, chat_id: int, delete_question=True):
    state = _state(app)
    _cancel_followups(app, chat_id)
    if delete_question:
        await _safe_delete_by_id(app.bot, chat_id, state.get("question_message_id"))
    state["active"] = False
    state["question_message_id"] = None


async def _daily_job(context: CallbackContext):
    chat_id = get_primary_chat_id()
    if not chat_id:
        return
    await _start_cycle(context.application, chat_id)


async def _followup_job(context: CallbackContext):
    app = context.application
    state = _state(app)
    chat_id = context.job.data.get("chat_id")
    if not state.get("active") or state.get("chat_id") != chat_id:
        context.job.schedule_removal()
        return
    await _send_question(app, chat_id)


async def _delete_message_job(context: CallbackContext):
    chat_id = context.job.data.get("chat_id")
    message_id = context.job.data.get("message_id")
    if not chat_id or not message_id:
        return
    await _safe_delete_by_id(context.bot, chat_id, message_id)


def ensure_daily_jobs(app: Application):
    state = _state(app)
    if state.get("daily_registered"):
        return
    jq = _job_queue(app)
    if jq is None:
        return

    tz = ZoneInfo(BOT_TIMEZONE)
    for hour in (10, 16, 22):
        jq.run_daily(
            _daily_job,
            time=dt.time(hour=hour, minute=0, tzinfo=tz),
            name=f"reminder_daily_{hour}",
        )
    state["daily_registered"] = True


async def on_startup_schedule(app: Application):
    ensure_daily_jobs(app)
    schedule_all_custom_reminders(app)
    chat_id = get_primary_chat_id()
    if chat_id:
        _state(app)["chat_id"] = chat_id


def remember_chat(chat_id: int):
    set_primary_chat_id(chat_id)


async def trigger_reminder_now(app: Application, chat_id: int):
    set_primary_chat_id(chat_id)
    await _start_cycle(app, chat_id)


async def handle_reminder_reply(update: Update, context: CallbackContext) -> None:
    if not update.message or not update.effective_chat:
        return

    state = _state(context.application)
    chat_id = update.effective_chat.id
    if not state.get("active") or state.get("chat_id") != chat_id:
        return

    # Во время выбора категории не перехватываем "да/нет" как ответ на напоминание.
    if context.user_data.get("pending_tx"):
        return

    answer = (update.message.text or "").strip().lower()
    if answer not in ("да", "нет"):
        return

    await _safe_delete_by_id(context.bot, chat_id, state.get("question_message_id"))
    await _safe_delete_by_id(context.bot, chat_id, update.message.message_id)
    state["question_message_id"] = None

    if answer == "да":
        await context.bot.send_message(chat_id=chat_id, text=YES_FOLLOWUP, reply_markup=build_main_keyboard())
        return

    await _stop_cycle(context.application, chat_id, delete_question=False)
    sent = await context.bot.send_message(
        chat_id=chat_id,
        text=NO_FOLLOWUP,
        reply_markup=build_main_keyboard(),
    )
    jq = _job_queue(context.application)
    if jq is None:
        return
    jq.run_once(
        _delete_message_job,
        when=dt.timedelta(minutes=15),
        data={"chat_id": chat_id, "message_id": sent.message_id},
        name=f"reminder_cleanup_{chat_id}_{sent.message_id}",
    )
