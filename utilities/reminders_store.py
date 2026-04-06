import json
import os
import uuid
from typing import Any

from config import BASE_DIR


REMINDERS_FILE = os.path.join(BASE_DIR, "data", "reminders.json")


def _read_payload(file_path=REMINDERS_FILE) -> dict[str, Any]:
    if not os.path.exists(file_path):
        return {"items": []}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            return {"items": []}
        if not isinstance(payload.get("items"), list):
            payload["items"] = []
        return payload
    except (OSError, json.JSONDecodeError):
        return {"items": []}


def _write_payload(payload: dict[str, Any], file_path=REMINDERS_FILE):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def list_reminders():
    payload = _read_payload()
    return payload.get("items", [])


def get_reminder(reminder_id: str):
    for item in list_reminders():
        if item.get("id") == reminder_id:
            return item
    return None


def upsert_reminder(reminder: dict[str, Any]):
    payload = _read_payload()
    items = payload.get("items", [])
    if not reminder.get("id"):
        reminder["id"] = f"r_{uuid.uuid4().hex[:10]}"

    replaced = False
    for idx, item in enumerate(items):
        if item.get("id") == reminder["id"]:
            items[idx] = reminder
            replaced = True
            break
    if not replaced:
        items.append(reminder)
    payload["items"] = items
    _write_payload(payload)
    return reminder


def delete_reminder(reminder_id: str):
    payload = _read_payload()
    before = len(payload.get("items", []))
    payload["items"] = [x for x in payload.get("items", []) if x.get("id") != reminder_id]
    _write_payload(payload)
    return len(payload["items"]) < before
