import re


def extract_signal_info(text):
    text = text.replace('"', '')
    # Регулярные выражения для извлечения данных
    signal_pattern = r"Сигнал:\s*(лонг|шорт)"
    entry_pattern = r"Вход:\s*([\d.]+)"
    sl_pattern = r"SL:\s*([\d.]+)"
    tp_pattern = r"TP:\s*([\d.]+)"
    rationale_pattern = r"Обоснование:\s*(.*)"

    # Извлечение данных
    signal_match = re.search(signal_pattern, text)
    entry_match = re.search(entry_pattern, text)
    sl_match = re.search(sl_pattern, text)
    tp_match = re.search(tp_pattern, text)
    # re.DOTALL для многострочного текста
    rationale_match = re.search(rationale_pattern, text, re.DOTALL)

    # Формирование результата
    result = {
        "Сигнал": signal_match.group(1).strip() if signal_match else None,
        "Вход": float(entry_match.group(1)) if entry_match else None,
        "SL": float(sl_match.group(1)) if sl_match else None,
        "TP": float(tp_match.group(1)) if tp_match else None,
        "Обоснование": rationale_match.group(1).strip() if rationale_match else None,
    }

    return result
