import json
import os
import re

from config import CATEGORY_MEMORY_FILE


def _normalize_description(text: str) -> str:
    value = (text or "").lower().replace("ё", "е")
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value, flags=re.UNICODE).strip()
    return value


def _load_memory(file_path=CATEGORY_MEMORY_FILE):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload.get("by_desc", {})


def _save_memory(by_desc, file_path=CATEGORY_MEMORY_FILE):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    payload = {"by_desc": by_desc}
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def learn_category(description: str, category: str):
    normalized = _normalize_description(description)
    if not normalized or not category:
        return
    by_desc = _load_memory()
    by_desc[normalized] = category
    _save_memory(by_desc)


def predict_category(description: str):
    normalized = _normalize_description(description)
    if not normalized:
        return None

    by_desc = _load_memory()
    if normalized in by_desc:
        return by_desc[normalized]

    current_words = set(normalized.split())
    best = (0.0, None)
    for desc, category in by_desc.items():
        words = set(desc.split())
        if not words:
            continue
        intersection = len(words & current_words)
        union = len(words | current_words)
        if union == 0:
            continue
        score = intersection / union
        if score > best[0]:
            best = (score, category)

    if best[0] >= 0.7:
        return best[1]
    return None
