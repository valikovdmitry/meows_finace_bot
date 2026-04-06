import json
import os

from config import RUNTIME_STATE_FILE


def load_runtime_state(file_path=RUNTIME_STATE_FILE):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_runtime_state(payload, file_path=RUNTIME_STATE_FILE):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def get_primary_chat_id():
    state = load_runtime_state()
    chat_id = state.get("primary_chat_id")
    if isinstance(chat_id, int):
        return chat_id
    return None


def set_primary_chat_id(chat_id: int):
    state = load_runtime_state()
    state["primary_chat_id"] = int(chat_id)
    save_runtime_state(state)
