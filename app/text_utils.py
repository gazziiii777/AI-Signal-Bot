import re


def extract_signal_info(text, timeframe):
    timeframe = timeframe.replace('.csv', '')
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

    signal = signal_match.group(1).strip() if signal_match else None
    entry = float(entry_match.group(1)) if entry_match else None
    sl = float(sl_match.group(1)) if sl_match else None
    tp = float(tp_match.group(1)) if tp_match else None
    rationale = rationale_match.group(1).strip() if rationale_match else None
    # Формирование результата
    text_to_send = f"Сигнал: {signal}\nВход: {entry}\nSL: {sl}\nTP: {tp}\nОбоснование: \n{rationale}\n #{timeframe}"

    db_data = {
        "timeframe": timeframe,
        "signal": signal,
        "open": entry,
        "SL": sl,
        "TP": tp,
        "status": 1,
        "pnl": 0
    }

    return text_to_send, db_data
