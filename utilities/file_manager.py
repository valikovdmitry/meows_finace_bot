import json
import os

from config import SHEETS_DUMP_FILE


# Функция записи актуального списка категорий в JSON-файл
def save_data_to_file(data, file_path = SHEETS_DUMP_FILE):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Данные успешно сохранены в {file_path}")

# Функция чтения актуального списка категорий в JSON-файл
def load_data_from_file(file_path = SHEETS_DUMP_FILE):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f)
            return {}
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

def clear_json_file(file_path = SHEETS_DUMP_FILE):
    """Очищает JSON-файл, записывая в него пустой объект {}"""
    try:
        if not os.path.exists(SHEETS_DUMP_FILE):  # Проверяем, существует ли файл
            print(f"⚠️ Файл {SHEETS_DUMP_FILE} не найден. Создаем новый.")

        with open(SHEETS_DUMP_FILE, "w", encoding="utf-8") as file:
            json.dump({}, file)  # Записываем пустой JSON-объект

        print(f"✅ Файл {SHEETS_DUMP_FILE} успешно очищен.")
    except Exception as e:
        print(f"❌ Ошибка при очистке файла {SHEETS_DUMP_FILE}: {e}")

