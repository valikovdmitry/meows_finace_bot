import datetime
from config import SPREADSHEET_ID


# Запись транзакции в таблицу
def write_transaction(amount, category, description, service):
    # Уникальный ID без дополнительного запроса к таблице.
    transaction_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    transaction_date = datetime.date.today().strftime("%d.%m.%Y")
    transaction_time = datetime.datetime.now().strftime("%H:%M:%S")

    data_to_write = [
        transaction_id,
        transaction_date,
        transaction_time,
        amount,
        category,
        description,
    ]

    response = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="A:F",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={
            "values": [data_to_write]
        },
    ).execute()

    updates = response.get("updates", {})
    updated_range = updates.get("updatedRange", "A:F")
    print(f"Данные записаны в диапазон {updated_range}: {data_to_write}")


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


def get_transactions(service, SPREADSHEET_ID):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="A2:F10000",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute()
    return result.get("values", [])


# if __name__ == '__main__':
#     write_transaction()
