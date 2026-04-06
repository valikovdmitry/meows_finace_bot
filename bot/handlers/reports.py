import asyncio
import datetime as dt

from telegram import Update
from telegram.ext import CallbackContext

from config import SPREADSHEET_ID
from sheets.auth import get_service
from sheets.sheets_manager import get_transactions
from utilities.text_process import find_category


def _load_transactions():
    service = get_service()
    rows = get_transactions(service, SPREADSHEET_ID)
    parsed = []
    for row in rows:
        if len(row) < 5:
            continue
        raw_date = str(row[1]).strip()
        raw_amount = row[3]
        raw_category = str(row[4]).strip()

        try:
            date = dt.datetime.strptime(raw_date, "%d.%m.%Y").date()
            amount = float(raw_amount)
        except (ValueError, TypeError):
            continue

        parsed.append(
            {
                "date": date,
                "amount": amount,
                "category": raw_category,
            }
        )
    return parsed


def _format_total_report(title, rows):
    total = sum(item["amount"] for item in rows)
    count = len(rows)
    return f"{title}\nТранзакций: {count}\nСумма: {total:,.0f} VND".replace(",", " ")


async def today_report(update: Update, context: CallbackContext) -> None:
    rows = await asyncio.to_thread(_load_transactions)
    today = dt.date.today()
    filtered = [item for item in rows if item["date"] == today]
    await update.effective_chat.send_message(_format_total_report("Отчет за сегодня", filtered))


async def week_report(update: Update, context: CallbackContext) -> None:
    rows = await asyncio.to_thread(_load_transactions)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    filtered = [item for item in rows if start <= item["date"] <= today]
    await update.effective_chat.send_message(_format_total_report("Отчет за неделю", filtered))


async def month_report(update: Update, context: CallbackContext) -> None:
    rows = await asyncio.to_thread(_load_transactions)
    today = dt.date.today()
    filtered = [item for item in rows if item["date"].year == today.year and item["date"].month == today.month]
    await update.effective_chat.send_message(_format_total_report("Отчет за месяц", filtered))


async def category_report(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.effective_chat.send_message("Используй так: /category аут")
        return

    query = " ".join(context.args).strip()
    resolved = find_category(query)
    if resolved == "- Нераспознанное":
        await update.effective_chat.send_message("Не смог распознать категорию.")
        return

    rows = await asyncio.to_thread(_load_transactions)
    filtered = [item for item in rows if item["category"] == resolved]
    title = f"Отчет по категории: {resolved[3:] if resolved.startswith(' - ') else resolved}"
    await update.effective_chat.send_message(_format_total_report(title, filtered))
