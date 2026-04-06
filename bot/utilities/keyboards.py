from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from utilities.file_manager import load_data_from_file


def get_categories_for_keyboard():
    categories = load_data_from_file() or {}
    result = []
    for key in categories.keys():
        if "нераспознан" in key.lower():
            continue
        result.append(key)
    return result


def build_category_keyboard(show_all=False):
    categories = get_categories_for_keyboard()
    if not show_all:
        categories = categories[:6]

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
    if not show_all and len(get_categories_for_keyboard()) > 6:
        rows.append([InlineKeyboardButton(text="Показать все", callback_data="cat_show_all")])
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


def build_main_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Update"), KeyboardButton("Тест")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
