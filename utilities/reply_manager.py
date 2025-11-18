def format_reply(m_sum, m_cat, m_desc):

    # Форматируем число, добавляем разделитель тысяч и два знака после запятой
    formatted_number = f"{float(m_sum):,.0f}"

    # Заменяем запятую на точку для разделителей тысяч
    formatted_number = formatted_number.replace(",", " ")
    formatted_number = formatted_number[:-3] + formatted_number[-3:].replace(".", ",")

    formated_vnd = sum_format(m_sum, 0)

    rub = m_sum / 1000 * 3
    formated_rub = sum_format(rub)

    usd = rub / 83
    formated_usd = sum_format(usd)

    if m_desc:
        text = f"Так и запишемс! 🐾 \n\n<b>{m_cat[3:]}</b>\n{formated_vnd} VND\n{formated_rub} ₽\n{formated_usd} $\n\nПримечание: {m_desc}\n\nМявс! 🐾"
    else:
        text = f"Так и запишемс! 🐾 \n\n<b>{m_cat[3:]}</b>\n{formated_vnd} VND\n\n\nМявс! 🐾"

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