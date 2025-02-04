import datetime
import gc

from config import SPREADSHEET_ID
from utilities.id_generator import get_id
from utilities.memory_manager import get_memory_usage, check_memory_limit


def write_transaction(amount, category, description, service, http_auth):
    id_dict = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="A1:A15000"
    ).execute()
    id_list = id_dict.get('values', [])


    get_memory_usage()

    gc.collect()

    first_empty_row =  len(id_list) + 1  # Первая свободная строка (1-based index)
    transaction_id = get_id(id_list)
    transaction_date = datetime.date.today().strftime('%d.%m.%Y')
    transaction_time = datetime.datetime.now().strftime('%H:%M:%S')

    print('---------- после получения ID ----------')


    using_memory = get_memory_usage()

    data_to_write = [transaction_id, transaction_date, transaction_time, amount, category, description, using_memory]  # Шесть колонок
    range_to_write = f"A{first_empty_row}:G{first_empty_row}"

    response = service.spreadsheets().values().update(
        spreadsheetId = SPREADSHEET_ID,
        range=range_to_write,
        valueInputOption="USER_ENTERED",
        body={
            "values": [data_to_write]
        }
    ).execute()
    print(f"Данные записаны в строку {first_empty_row}: {data_to_write}")

    http_auth.close()
    gc.collect()

    print('---------- после записи данных ----------')
    #get_memory_usage()

    # Рестартим если используемая память больше 300мб
    check_memory_limit(service, http_auth)
    return

def test_transaction_stream(service, http_auth, amount='150', category='- Продукты', description='тест'):
    for i in range(0,15000):
        #asyncio.run( asyncio.sleep(1))
        print(f'\ntest')
        write_transaction('150', '- Продукты', 'тест', service, http_auth)


# Удаление последней транзакции
def delete_last_transaction(service, http_auth, SPREADSHEET_ID):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="A1:A1000"  # Ограничиваем диапазон строками 1-1000
    ).execute()

    # Проверяем, сколько строк заполнено
    values = result.get('values', [])
    if values:
        last_filled_row = len(values)
        range_to_clear = f"A{last_filled_row}:Z{last_filled_row}"

        # Очищаем строку
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=range_to_clear
        ).execute()

        http_auth.close()
        gc.collect()

        print(f"Строка {last_filled_row} была очищена.")
    else:
        http_auth.close()
        gc.collect()

        print("Нет заполненных строк.")


# Функция получения актуального списка категорий
def load_categories(service, http_auth, SPREADSHEET_ID):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Категории!A2:B23"
    ).execute()
    values = result.get('values', [])

    http_auth.close()
    gc.collect()

    dict_val = {}
    for i in values:
        dict_val[i[0]] = i[1]

    return dict_val