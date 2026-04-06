from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utilities.file_manager import load_data_from_file


def get_categories_for_keyboard():
    categories = load_data_from_file() or {}
    result = []
    for key in categories.keys():
        if "нераспознан" in key.lower():
            continue
        result.append(key)
    return result


def build_category_keyboard():
    categories = get_categories_for_keyboard()
    rows = []
    row = []
    for idx, category in enumerate(categories):
        row.append(
            InlineKeyboardButton(
                text=category[3:] if category.startswith(" - ") else category,
                callback_data=f"catidx:{idx}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="cat_cancel")])
    return InlineKeyboardMarkup(rows)


def build_post_save_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="↩️ Отменить", callback_data="undo_last"),
                InlineKeyboardButton(text="✏️ Изменить категорию", callback_data="edit_last"),
            ]
        ]
    )
