import openai
import pandas as pd
from pathlib import Path


class CSVAnalyzerGPT:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
        # Фиксированная директория
        self.downloads_dir = Path("/root/scripts/AI-Signal-Bot/app/downloads")

    def _csvs_to_text(self, csv_file_names):
        csv_texts = []
        for i, file_name in enumerate(csv_file_names, start=1):
            file_path = self.downloads_dir / file_name  # Формируем полный путь
            if not file_path.exists():  # Проверяем, существует ли файл
                print(f"Файл {file_name} не найден, пропускаем.")
                continue

            # Читаем первую строку и последние 100 строк
            with open(file_path, mode="r", encoding="utf-8") as file:
                first_line = file.readline()  # Читаем первую строку
                lines = file.readlines()  # Читаем все оставшиеся строки

            # Получаем последние 100 строк (или меньше, если файл маленький)
            last_100_lines = lines[-100:] if len(lines) >= 100 else lines

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

    def ask_gpt_about_csvs(self, csv_file_names, question, model_name):
        csv_text = self._csvs_to_text(csv_file_names)

        prompt = f"""
        У меня есть следующие данные, извлеченные из CSV-файлов, Файл 1 - это 15 минутный таймфрейм, Файл 2- это 60 минутный  таймфрейм, Файл 3 - это 240 минутный таймфрейм. 

        {csv_text}

        Исходя из этих данных ответь на следующий вопрос: {question}":
        
        """

        response = self.client.chat.completions.create(
            model=model_name,  # или "gpt-3.5-turbo"
            messages=[
                {"role": "system",
                    "content": "Выступи в роли профессионального трейдера-аналитика"},
                {"role": "user", "content": prompt},
            ],
            reasoning_effort="high"
        )

        return response.choices[0].message.content
