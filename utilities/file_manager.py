import json
import os


# Функция записи актуального списка категорий в JSON-файл
def save_data_to_file(data, file_path = os.path.join("../data", "sheets_dump.json")):
    # Проверяем, существует ли папка
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Записываем данные
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)  # indent=4 делает JSON красивым
    print(f"Данные успешно сохранены в {file_path}")

# Функция чтения актуального списка категорий в JSON-файл
def load_data_from_file(file_path = 'data/sheets_dump.json'):
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден.")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    #print(f"Данные успешно загружены из {file_path}")
    return data