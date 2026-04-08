def format_reply(m_sum, m_cat, m_desc, elapsed_seconds=None):
    rub = float(m_sum)
    vnd = rub / 3 * 1000
    formatted_rub = sum_format(rub)
    formatted_vnd = sum_format(vnd, 0)
    category_label = m_cat[3:] if m_cat.startswith(" - ") else m_cat
    note = m_desc if m_desc else "—"

    version_line = "Версия 1.1"
    if elapsed_seconds is not None:
        version_line = f"Версия 1.1 • {elapsed_seconds:.2f} сек"

    text = (
        f"<b>{category_label}</b>\n"
        f"Примечание: {note}\n\n"
        f"{formatted_rub} ₽\n"
        f"{formatted_vnd} VND\n\n"
        f"{version_line}"
    )

    return text

def sum_format(sum, n=2):
    # Форматируем число, добавляем разделитель тысяч и два знака после запятой
    if n == 0:
        formatted_number = f"{float(sum):,.0f}"
    else:
        formatted_number = f"{float(sum):,.2f}"

    # Заменяем запятую на точку для разделителей тысяч
    formatted_number = formatted_number.replace(",", " ")
    formatted_number = formatted_number[:-3] + formatted_number[-3:].replace(".", ",")

    return formatted_number
