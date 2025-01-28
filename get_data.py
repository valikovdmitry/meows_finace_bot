# Функция получения актуального списка категорий
from auth import get_service
from find_first_empty_row import find_first_empty_row
from load_from_env import spreadsheets_id


def get_data_from_sheets():
    SPREADSHEET_ID = spreadsheets_id
    service = get_service()
    last_row = find_first_empty_row() - 1

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"A1:F{last_row}"
    ).execute()

    values = result.get('values', [])

    # Проверяем, есть ли данные
    if values:
        # Преобразуем строки (rows) в столбцы (columns)
        columns = list(zip(*values))  # Используем zip и распаковку
        print(columns)
    else:
        print("No data found.")

    return values


print(get_data_from_sheets())


import plotly.graph_objects as go



# Ваши данные в виде строк
data = get_data_from_sheets()


# Разделяем заголовки и строки
headers = data[0]  # Первая строка — это заголовки
columns = data[1:]    # Остальные строки — содержимое


# Выводим для проверки
print("Headers:", headers)
print("Columns:")
# for i, col in enumerate(columns):
#     print(f"{headers[i]}: {col}")

# Создаем таблицу
fig = go.Figure(data=[go.Table(
    header=dict(
        values=columns,            # Заголовки колонок
        fill_color="lightblue",    # Цвет фона заголовков
        align="center",            # Выравнивание текста в заголовках
        font=dict(color="black", size=12)  # Шрифт заголовков
    ),
    cells=dict(
        values=headers,            # Данные в колонках
        fill_color="white",        # Цвет фона ячеек
        align="center",            # Выравнивание текста в ячейках
        font=dict(color="black", size=11)  # Шрифт ячеек
    )
)])

# Добавляем заголовок (опционально)
fig.update_layout(title="Table from Rows Data")

# Показываем таблицу
fig.show()