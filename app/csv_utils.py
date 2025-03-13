def csvs_to_text(csv_file_names, downloads_dir):
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
        last_100_lines = lines[-300:] if len(lines) >= 300 else lines

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