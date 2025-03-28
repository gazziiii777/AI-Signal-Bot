import sqlite3
import os
from db_config import TABLES


class DatabaseManager:
    def __init__(self, db_path):
        """
        Инициализация класса с путем к базе данных.
        :param db_path: Путь к файлу базы данных.
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Подключение к базе данных.
        """
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Подключаемся к базе данных
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        print(
            f"Подключение к базе данных '{self.db_path}' успешно установлено.")

    def create_table(self, table_name, columns):
        """
        Создание таблицы в базе данных.
        :param table_name: Имя таблицы (например, 'users')
        :param columns: Словарь с именами колонок и их типами (например, {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT', 'age': 'INTEGER'})
        """
        if not self.connection:
            raise Exception(
                "Сначала подключитесь к базе данных, используйте метод connect().")

        # Формируем SQL-запрос для создания таблицы
        columns_with_types = [
            f"{col_name} {col_type}" for col_name, col_type in columns.items()]
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_with_types)});"

        # Выполняем запрос
        self.cursor.execute(create_table_query)
        self.connection.commit()
        print(f"Таблица '{table_name}' успешно создана.")

    def close(self):
        """
        Закрытие соединения с базой данных.
        """
        if self.connection:
            self.connection.close()
            print(f"Соединение с базой данных '{self.db_path}' закрыто.")
        else:
            print("Соединение с базой данных уже закрыто.")

    def insert_data(self, table_name, data):
        """
        Вставка данных в таблицу.
        :param table_name: Имя таблицы, в которую нужно вставить данные.
        :param data: Словарь с данными для вставки (ключи - имена колонок, значения - данные).
        """
        if not self.connection:
            raise Exception(
                "Сначала подключитесь к базе данных, используйте метод connect().")

        # Проверяем, что таблица существует в конфигурации
        if table_name not in TABLES:
            raise ValueError(
                f"Таблица '{table_name}' не найдена в конфигурации.")

        # Проверяем, что все ключи в data соответствуют колонкам таблицы
        table_columns = TABLES[table_name].keys()
        for key in data.keys():
            if key not in table_columns:
                raise ValueError(
                    f"Колонка '{key}' не найдена в таблице '{table_name}'.")

        # Формируем SQL-запрос для вставки данных
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"

        # Выполняем запрос
        self.cursor.execute(insert_query, tuple(data.values()))
        self.connection.commit()
        print(f"Данные успешно вставлены в таблицу '{table_name}'.")

    def has_status_zero(self, table_name, timeframe, coin_name):
        """
        Проверяет, есть ли в таблице хотя бы одна запись с колонкой status = 0.
        Если найдена запись с status = 0, возвращает значения SL, TP и signal.
        Если таблица пустая или не существует, возвращает None.
        :param table_name: Имя таблицы для проверки.
        :param timeframe: Таймфрейм для фильтрации.
        :return: Словарь с ключами 'SL', 'TP', 'signal', если найдена запись с status = 0, иначе None.
        """
        if not self.connection:
            raise Exception(
                "Сначала подключитесь к базе данных, используйте метод connect().")

        # Проверяем, есть ли записи в таблице
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = self.cursor.fetchone()[0]

        if row_count == 0:
            print(f"Таблица '{table_name}' пустая.")
            return False  # Если таблица пустая, возвращаем False

        # Ищем запись с status = 0 и указанным timeframe
        query = f"""
            SELECT SL, TP, signal, open
            FROM {table_name} 
            WHERE status = 1 AND timeframe = ? AND coin_name = ?
            LIMIT 1;
        """
        self.cursor.execute(query, (timeframe, coin_name))  # Передаем два параметра
        result = self.cursor.fetchone()
        if result:
            # Если запись найдена, возвращаем SL, TP и signal
            sl, tp, signal, open = result
            return {"SL": sl, "TP": tp, "signal": signal, "open": open}
        else:
            # Если запись не найдена, возвращаем None
            return False

    def update_status_and_pnl(self, table_name, timeframe, pnl, coin_name):
        """
        Обновляет статус на 0 и записывает значение pnl для всех записей с status = 1 и указанным timeframe.
        :param table_name: Имя таблицы для обновления.
        :param timeframe: Таймфрейм для фильтрации записей.
        :param pnl: Значение Profit and Loss (pnl), которое нужно записать.
        :return: Количество обновленных строк.
        """
        if not self.connection:
            raise Exception(
                "Сначала подключитесь к базе данных, используйте метод connect().")

        # Проверяем, существует ли столбец pnl, и если нет, добавляем его
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [column[1] for column in self.cursor.fetchall()]
        if "pnl" not in columns:
            self.cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN pnl REAL;")
            self.connection.commit()  # Фиксируем изменения в структуре таблицы

        update_query = f"""
            UPDATE {table_name} 
            SET status = 0, pnl = ? 
            WHERE status = 1 AND timeframe = ? AND coin_name = ?;
        """
        self.cursor.execute(update_query, (pnl, timeframe, coin_name))
        self.connection.commit()  # Фиксируем изменения в данных

        # Возвращаем количество обновленных строк
        return self.cursor.rowcount

    def get_total_pnl(self, table_name, timeframe=None):
        """
        Возвращает сумму всех значений в столбце pnl для указанной таблицы.
        :param table_name: Имя таблицы, из которой нужно получить сумму pnl.
        :param timeframe: (опционально) Таймфрейм для фильтрации данных. Если None, суммируются все строки.
        :return: Сумма всех значений в столбце pnl. Если столбец отсутствует или таблица пуста, возвращает 0.
        """
        if not self.connection:
            raise Exception(
                "Сначала подключитесь к базе данных, используйте метод connect().")

        # Проверяем, существует ли столбец pnl
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [column[1] for column in self.cursor.fetchall()]
        if "pnl" not in columns:
            print(f"Столбец 'pnl' отсутствует в таблице {table_name}.")
            return 0

        # Базовый запрос для получения суммы всех значений в столбце pnl
        sum_pnl_query = f"""
            SELECT SUM(pnl) 
            FROM {table_name}
        """

        # Если передан таймфрейм, добавляем условие WHERE для фильтрации
        if timeframe:
            sum_pnl_query += f" WHERE timeframe = '{timeframe}'"

        self.cursor.execute(sum_pnl_query)
        sum_pnl = self.cursor.fetchone()[0]  # Получаем сумму pnl

        # Если сумма равна None (например, если таблица пуста), возвращаем 0
        return sum_pnl or 0