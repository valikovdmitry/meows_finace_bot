from utilities.id_generator import get_id
import datetime
from config import SPREADSHEET_ID


# Запись транзакции в таблицу
def write_transaction(amount, category, description, service):
    # Получаем данные из первой колонки таблицы в виде листа
    id_dict = service.spreadsheets().values().get(
        spreadsheetId = SPREADSHEET_ID,
        range="A1:A1000"  # Ограничиваем диапазон строками 1-1000
    ).execute()
    id_list = id_dict.get('values', [])

    first_empty_row =  len(id_list) + 1  # Первая свободная строка (1-based index)

    transaction_id = get_id(id_list)
    transaction_date = datetime.date.today().strftime('%d.%m.%Y')
    transaction_time = datetime.datetime.now().strftime('%H:%M:%S')

    data_to_write = [transaction_id, transaction_date, transaction_time, amount, category, description]  # Шесть колонок

    range_to_write = f"A{first_empty_row}:F{first_empty_row}"

    response = service.spreadsheets().values().update(
        spreadsheetId = SPREADSHEET_ID,
        range=range_to_write,
        valueInputOption="USER_ENTERED",
        body={
            "values": [data_to_write]
        }
    ).execute()

    print(f"Данные записаны в строку {first_empty_row}: {data_to_write}")


# Удаление последней транзакции
def delete_last_transaction(service, SPREADSHEET_ID):
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
        range_to_clear = f"A{last_filled_row}:Z{last_filled_row}"

        # Очищаем строку
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=range_to_clear
        ).execute()
        print(f"Строка {last_filled_row} была очищена.")
    else:
        print("Нет заполненных строк.")


# Функция получения актуального списка категорий
def get_categories(service, SPREADSHEET_ID):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Категории!A2:B23"
    ).execute()
    values = result.get('values', [])
    dict_val = {}
    for i in values:
        dict_val[i[0]] = i[1]
    return dict_val


# if __name__ == '__main__':
#     write_transaction()