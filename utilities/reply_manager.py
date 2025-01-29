

def format_reply(m_sum, m_cat, m_desc):
    # Форматируем число, добавляем разделитель тысяч и два знака после запятой
    formatted_number = f"{float(m_sum):,.2f}"
    # Заменяем запятую на точку для разделителей тысяч
    formatted_number = formatted_number.replace(",", " ")
    formatted_number = formatted_number[:-3] + formatted_number[-3:].replace(".", ",")

    if m_desc:
        text = f"Так и запишемс! 🐾 \n\n<b>{m_cat[3:]}</b>\n{formatted_number} ₽\nПримечание: {m_desc}\n\nМявс!"
    else:
        text = f"Так и запишемс! 🐾 \n\n<b>{m_cat[3:]}</b>\n{formatted_number} ₽\n\n\nМявс!"

    return text