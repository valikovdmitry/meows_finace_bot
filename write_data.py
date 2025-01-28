from auth import get_service
from id_generator import id_gen
import datetime
from load_from_env import spreadsheets_id

# Получаем текущую дату и время
current_date_source = datetime.date.today()
current_date = current_date_source.strftime('%d.%m.%Y')
current_time_str = datetime.datetime.now().strftime('%H:%M:%S')


def write_to_first_empty_row(transaction_amount, transaction_category, transaction_description):
    # Авторизация Google API
    service = get_service()

    # Получаем данные из первой колонки таблицы в виде листа
    id_dict = service.spreadsheets().values().get(
        spreadsheetId = spreadsheets_id,
        range="A1:A1000"  # Ограничиваем диапазон строками 1-1000
    ).execute()
    id_list = id_dict.get('values', [])

    first_empty_row =  len(id_list) + 1  # Первая свободная строка (1-based index)

    transaction_id = id_gen(id_list)
    transaction_date = current_date
    transaction_time = current_time_str

    data_to_write = [transaction_id, transaction_date, transaction_time, transaction_amount, transaction_category, transaction_description]  # Шесть колонок

    range_to_write = f"A{first_empty_row}:F{first_empty_row}"

    response = service.spreadsheets().values().update(
        spreadsheetId = spreadsheets_id,
        range=range_to_write,
        valueInputOption="USER_ENTERED",
        body={
            "values": [data_to_write]
        }
    ).execute()

    print(f"Данные записаны в строку {first_empty_row}: {data_to_write}")

if __name__ == '__main__':
    write_to_first_empty_row()