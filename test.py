from func_sheets import load_data_from_file


def find_keywords_in_message(message, keyword_dict):
    # Разделяем сообщение на слова
    message_lower = message.lower()
    words = message_lower.split()
    print(words)

    # Результирующий список категорий
    categories = []

    # Преобразуем ключевые слова в список для упрощенной проверки длины
    keyword_list = list(keyword_dict.keys())
    #print(keyword_list)

    # Проходим по словам в сообщении
    i = 0
    success = 0
    while i < len(words) and success == 0:
        for keyword in keyword_list:
            #print(keyword)
            # Разделяем ключевое слово на части (для многословных ключей)
            keyword_parts = keyword.split()

            # Проверяем, совпадает ли фрагмент сообщения с ключевым словом
            if words[i:i + len(keyword_parts)] == keyword_parts:
                # Если нашли, добавляем категорию
                cat = keyword_dict[keyword]
                success = 1
                break

        i += 1  # Если ничего не нашли, идем к следующему слову

    return cat


# Пример использования
message = "234.45 фрукты творог для дома продукты"
keyword_dict = load_data_from_file()

# Преобразуем словарь для удобства поиска
expanded_keyword_dict = {}
for category, keywords in keyword_dict.items():
    for keyword in keywords.split(", "):
        expanded_keyword_dict[keyword.lower()] = category

categories = find_keywords_in_message(message, expanded_keyword_dict)

print(categories)
