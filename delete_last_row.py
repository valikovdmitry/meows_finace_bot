from auth import get_service
from load_from_env import spreadsheets_id

SPREADSHEET_ID = spreadsheets_id


def clear_last_filled_row():
    service = get_service()
    """
    Находит последнюю заполненную строку на листе и очищает её.
    """
    # Считываем столбец A до строки 1000 (можно увеличить число строк)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="A1:A1000"  # Ограничиваем диапазон строками 1-1000
    ).execute()

    # Проверяем, сколько строк заполнено
    values = result.get('values', [])

    # Если есть данные, находим последнюю заполненную строку
    if values:
        last_filled_row = len(values)

        # Очищаем эту строку (например, очищаем все столбцы в строке)
        range_to_clear = f"A{last_filled_row}:Z{last_filled_row}"  # Можно изменить диапазон столбцов (например, A-Z)

        # Очищаем строку
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=range_to_clear
        ).execute()
        print(f"Строка {last_filled_row} была очищена.")
    else:
        print("Нет заполненных строк.")


if __name__ == '__main__':
    clear_last_filled_row()