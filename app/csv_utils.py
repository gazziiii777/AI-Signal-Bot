from pathlib import Path


def csvs_to_text(csv_file_names, downloads_dir, max_row):
    """
    Функция для преобразования CSV-файлов в текстовый формат.
    :param csv_file_names: Список имен CSV-файлов.
    :param downloads_dir: Путь к директории с файлами.
    :return: Текстовое представление данных из CSV-файлов.
    """
    csv_texts = []
    for i, file_name in enumerate(csv_file_names, start=1):
        file_path = downloads_dir / file_name  # Формируем полный путь
        if not file_path.exists():  # Проверяем, существует ли файл
            print(f"Файл {file_name} не найден, пропускаем.")
            continue

        # Читаем первую строку и последние 100 строк
        with open(file_path, mode="r", encoding="utf-8") as file:
            first_line = file.readline()  # Читаем первую строку
            lines = file.readlines()  # Читаем все оставшиеся строки

        # Получаем последние 100 строк (или меньше, если файл маленький)
        last_100_lines = lines[-max_row:] if len(lines) >= max_row else lines

        # Оборачиваем первую строку и последние 100 строк в фигурные кавычки {}
        wrapped_lines = [f"{{{first_line.strip()}}}"] + \
                        [f"{{{line.strip()}}}" for line in last_100_lines]

        # Добавляем результат в список
        csv_texts.append(
            f"Файл {i} ({file_name}):\n" + "\n".join(wrapped_lines))

    if not csv_texts:  # Если ни один файл не был обработан
        return "Нет данных для анализа.", None

    # Объединяем все строки в один текст
    result_text = "\n".join(csv_texts)

    # Синхронное сохранение результата в файл
    with open("csv_output.txt", mode="w", encoding="utf-8") as f:
        f.write(result_text)

    return result_text


def get_last_high_low(file_name, downloads_dir):
    """
    Функция для получения значений high и low из последней строки CSV-файла.
    :param downloads_dir: Путь к директории с файлом.
    :param file_name: Имя CSV-файла.
    :return: Кортеж (high, low) или None, если данные недоступны.
    """
    file_path = downloads_dir / file_name  # Формируем полный путь

    # Проверяем, существует ли файл и не является ли он директорией
    if not file_path.exists():
        print(f"Файл {file_name} не найден в директории {downloads_dir}.")
        return None
    if file_path.is_dir():  # Проверяем, что это не директория
        print(f"Указанный путь {file_path} является директорией, а не файлом.")
        return None

    # Читаем последнюю строку из файла
    with open(file_path, mode="r", encoding="utf-8") as file:
        lines = file.readlines()  # Читаем все строки
        if not lines:  # Если файл пустой
            print(f"Файл {file_name} пуст.")
            return None

        # Получаем заголовки (первую строку)
        headers = lines[0].strip().split(",")
        if 'high' not in headers or 'low' not in headers:  # Проверяем наличие столбцов
            print(f"Файл {file_name} не содержит столбцов high и low.")
            return None

        # Получаем последнюю строку
        last_line = lines[-1].strip().split(",")

        # Находим индексы столбцов high и low
        high_index = headers.index('high')
        low_index = headers.index('low')

        # Извлекаем значения high и low
        high_value = last_line[high_index]
        low_value = last_line[low_index]

    return high_value, low_value
