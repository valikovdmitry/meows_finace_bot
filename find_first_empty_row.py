from auth import get_service
from load_from_env import spreadsheets_id

SPREADSHEET_ID = spreadsheets_id

def find_first_empty_row():
    service = get_service()
    """
    Определяет первую свободную строку на указанном листе.
    """
    # Считываем столбец A до строки 1000 (можно увеличить число строк)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="A1:A1000"  # Ограничиваем диапазон строками 1-1000
    ).execute()

    # Проверяем, сколько строк заполнено
    values = result.get('values', [])
    return len(values) + 1  # Первая свободная строка (1-based index)


if __name__ == '__main__':
    find_first_empty_row()