from pathlib import Path
import openai
from app.csv_utils import csvs_to_text, get_last_high_low


class CSVAnalyzerGPT:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
        # Фиксированная директория
        self.downloads_dir = Path("/root/scripts/AI-Signal-Bot/app/downloads")

    def ask_gpt_about_csvs(self, csv_file_names, question, model_name, max_row):
        # Используем функцию из csv_utils.py
        csv_text = csvs_to_text(csv_file_names, self.downloads_dir, max_row)
        # high_value, low_value = get_last_high_low(
        #     csv_file_names[0], self.downloads_dir)
        # print(high_value, low_value)
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
            # reasoning_effort="high"
        )

        return response.choices[0].message.content
