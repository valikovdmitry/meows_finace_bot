

from utilities.file_manager import load_data_from_file


def find_args(text):
    # Разбиваем строку на части по запятой
    data_parts = [part.strip() for part in text.split(" ")]

    sum = 0
    # находим первый int или не str = сумма
    for word in data_parts:
        if word.isdigit():
            sum = float(word)
            data_parts.remove(word)
            break
        if not word.isalpha():
            word_pre_convert = word.replace(",", ".")
            data_parts.remove(word)
            sum = float(word_pre_convert)
            break

    if not sum:
        return 0, 0, 0

    text = " ".join(data_parts)

    dict_val = load_data_from_file()

    result_options = []

    for key, value in dict_val.items():
        clean_value_lower = value.lower()
        clean_value_list = [part.strip() for part in clean_value_lower.split(",")]

        for item in clean_value_list:

            if item in text.lower() and item:
                result_options.append((text.lower().index(item), len(item), key))

    if not result_options:
        cat = '- Нераспознанное'
        return sum, cat, text

    result = result_options[0]

    for idx, lens, cat in result_options:
        if idx < result[0]:
            result = (idx, lens, cat)

    text = text[:result[0]] + text[result[0] + result[1] + 1:]
    cat = result[2]

    return sum, cat, text


def find_category(text):
    dict_val = load_data_from_file()
    result_options = []

    for key, value in dict_val.items():
        clean_value_lower = value.lower()
        clean_value_list = [part.strip() for part in clean_value_lower.split(",")]

        for item in clean_value_list:

            if item in text.lower() and item:
                result_options.append((text.lower().index(item), len(item), key))

    if not result_options:
        cat = '- Нераспознанное'
        return cat

    result = result_options[0]

    for idx, lens, cat in result_options:
        if idx < result[0]:
            result = (idx, lens, cat)

    text = text[:result[0]] + text[result[0] + result[1] + 1:]
    cat = result[2]

    return cat

#print(find_args(text))