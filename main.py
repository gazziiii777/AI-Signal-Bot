import asyncio
from aiogram import Bot, Dispatcher
from datetime import datetime, timedelta
import pytz  # Для работы с временными зонами
from app.tradingview import TradingViewButtonClicker
from app.gpt import CSVAnalyzerGPT
import prompts
import logging
import re  # Импортируем модуль для работы с регулярными выражениями
from dotenv import load_dotenv
import os
import config
from app.text_utils import extract_signal_info
from db_config import DB_PATH, TABLES  # Импортируем константы
from app.db.database_manager import DatabaseManager
from app.csv_utils import get_last_high_low
from pathlib import Path


# Загрузка переменных окружения из .env файла
load_dotenv()


# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Устанавливаем временную зону (Москва)
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()


async def run_every_15_minutes():
    """Функция, которая выполняется каждые 15 минут в определённое время."""
    try:
        logging.info("Запуск задач каждые 15 минут...")
        button_clicker = TradingViewButtonClicker(
            config.USER_DATA_DIR,
            config.DOWNLOADS_DIR, config.COOKIES_FILE
        )

        await button_clicker.open_browser()
        await button_clicker.open_tabs()

        tasks = []
        for tab_index in range(len(button_clicker.pages)):
            tasks.append(asyncio.create_task(
                button_clicker.perform_actions_in_tab_15_min(tab_index)))

        await asyncio.gather(*tasks)
        logging.info("Задачи каждые 15 минут успешно выполнены.")

    except FileNotFoundError as e:
        logging.error(f"Файл не найден: {e}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        if 'button_clicker' in locals():
            await button_clicker.close_browser()
            logging.info(
                "Браузер закрыт после выгрузки задач каждые 15 минут.")


async def run_every_hour():
    """Функция, которая выполняется каждый час в определённое время."""
    try:
        logging.info("Запуск задач каждый час...")
        button_clicker = TradingViewButtonClicker(
            config.USER_DATA_DIR,
            config.DOWNLOADS_DIR, config.COOKIES_FILE
        )

        await button_clicker.open_browser()
        await button_clicker.open_tabs()

        tasks = []
        for tab_index in range(len(button_clicker.pages)):
            tasks.append(asyncio.create_task(
                button_clicker.perform_actions_in_tab_1_hour(tab_index)))

        await asyncio.gather(*tasks)
        logging.info("Задачи каждый час успешно выполнены.")

    except FileNotFoundError as e:
        logging.error(f"Файл не найден: {e}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        if 'button_clicker' in locals():
            await button_clicker.close_browser()
            logging.info("Браузер закрыт после выгрузки задач каждый час.")


def pnl_update(first_prise, second_prise, db_manager, db_name, file_name, pnl_status, coin_name):
    text_to_send = ''
    pnl = round(((first_prise - second_prise) / second_prise) * 100, 3)
    # Если pnl_status равно False, делаем pnl отрицательным
    if not pnl_status:
        pnl = -abs(pnl)
        db_manager.update_status_and_pnl(db_name, file_name, pnl, coin_name)
        total_pnl = db_manager.get_total_pnl(db_name, file_name)
        text_to_send = f'Сделка закрыта по стоп-лоссу. PNL {pnl}%\nКумулятивный PNL {round(float(total_pnl), 3)}%\n\n#{file_name}'
    else:
        pnl = abs(pnl)
        db_manager.update_status_and_pnl(db_name, file_name, pnl, coin_name)
        total_pnl = db_manager.get_total_pnl(db_name, file_name)
        text_to_send = f'Сделка закрыта по тейк-профиту. PNL {pnl}%\nКумулятивный PNL {round(float(total_pnl), 3)}%\n\n#{file_name}'

    return text_to_send


async def signal_and_send_message(file_names, prompt, model_name, chanel_id, max_row, coin_name, db_name):
    """Третья функция, которая выполняется после первой или второй."""
    timeframe = file_names[0].split("_")[0]
    RR_name = db_name.replace(db_name, "3")
    db_manager = DatabaseManager(DB_PATH)
    db_manager.connect()
    position_open = db_manager.has_status_zero(
        db_name, timeframe, coin_name)
    if not position_open:
        analyzer = CSVAnalyzerGPT(api_key=os.getenv("API_KEY"))
        answer = analyzer.ask_gpt_about_csvs(
            file_names, prompt, model_name, max_row)

        logging.info(answer)
        # Извлекаем текст, заключённый в {}
        matches = re.findall(r"\{([^}]+)\}", answer)
        if matches:
            # Объединяем все найденные фрагменты в одну строку
            format_text = "\n".join(matches)
            try:
                text_to_send, db_data = extract_signal_info(
                    format_text, timeframe, coin_name, RR_name)
                if db_data['signal'] != None:
                    db_manager.insert_data(db_name, db_data)
                    await bot.send_message(chat_id=chanel_id, text=text_to_send)
                    logging.info(
                        "Сообщение успешно отправлено в Telegram-канал.")

            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        else:
            format_text = None
    else:
        # print(position_open)
        high_value, low_value = get_last_high_low(
            file_names[0], Path("/root/scripts/AI-Signal-Bot/app/downloads"))
        # print(high_value, low_value)
        if position_open['signal'] == "шорт" or position_open['signal'] == "short":
            if position_open['TP'] > low_value:
                text_to_send = pnl_update(position_open['open'], position_open['TP'],
                                          db_manager, db_name, timeframe, True, coin_name)
                await bot.send_message(chat_id=chanel_id, text=text_to_send)
            if position_open['SL'] < high_value:
                text_to_send = pnl_update(position_open['open'], position_open['SL'],
                                          db_manager, db_name, timeframe, False, coin_name)
                await bot.send_message(chat_id=chanel_id, text=text_to_send)
        else:
            if position_open['TP'] < high_value:
                text_to_send = pnl_update(position_open['TP'], position_open['open'],
                                          db_manager, db_name, timeframe, True, coin_name)
                await bot.send_message(chat_id=chanel_id, text=text_to_send)
            if position_open['SL'] > low_value:
                text_to_send = pnl_update(position_open['open'], position_open['SL'],
                                          db_manager, db_name, timeframe, False, coin_name)
                await bot.send_message(chat_id=chanel_id, text=text_to_send)

    logging.info("Третья функция завершена.")


async def scheduler():
    """Планировщик задач."""
    while True:
        now = datetime.now(MOSCOW_TZ)  # Текущее время по МСК
        minute = now.minute
        hour = now.hour

        # Запуск каждые 15 минут (в :13, :28, :43, :58)
        if minute in {12, 28, 43, 58}:
            await run_every_15_minutes()  # Запуск первой функции
            # Запуск третьей функции после первой
            await signal_and_send_message(["M15_BTC.csv", "H1_BTC.csv", "H4_BTC.csv"], prompts.prompt_M15_RR3, "o1", os.getenv("RR3_CHANEL_ID"), config.O1_MAX_ROW, 'BTC', 'RR3')
            await signal_and_send_message(["M15_ETH.csv", "H1_ETH.csv", "H4_ETH.csv"], prompts.prompt_M15_RR3, "o1", os.getenv("RR3_CHANEL_ID"), config.O1_MAX_ROW, 'ETH', 'RR3')
            await signal_and_send_message(["M15_SOL.csv", "H1_SOL.csv", "H4_SOL.csv"], prompts.prompt_M15_RR3, "o1", os.getenv("RR3_CHANEL_ID"), config.O1_MAX_ROW, 'SOL', 'RR3')
            await signal_and_send_message(["M15_BTC.csv", "H1_BTC.csv", "H4_BTC.csv"], prompts.prompt_H1_RR3, "o1", os.getenv("RR5_CHANEL_ID"), config.O1_MAX_ROW, 'BTC', 'RR5')
            await signal_and_send_message(["M15_ETH.csv", "H1_ETH.csv", "H4_ETH.csv"], prompts.prompt_H1_RR3, "o1", os.getenv("RR5_CHANEL_ID"), config.O1_MAX_ROW, 'ETH', 'RR5')
            await signal_and_send_message(["M15_SOL.csv", "H1_SOL.csv", "H4_SOL.csv"], prompts.prompt_H1_RR3, "o1", os.getenv("RR5_CHANEL_ID"), config.O1_MAX_ROW, 'SOL', 'RR5')
            # await signal_and_send_message(["M15.csv", "H1.csv", "H4.csv"], prompts.prompt_M15, "o3-mini", os.getenv("O3_MINI_CHANEL_ID"), config.O3_MINI_MAX_ROW)

        # Запуск каждый час в :58
        if minute == 58:
            await run_every_hour()  # Запуск второй функции
            await signal_and_send_message(["H1_BTC.csv", "H4_BTC.csv", "D1_BTC.csv"], prompts.prompt_M15_RR5, "o1", os.getenv("RR3_CHANEL_ID"), config.O1_MAX_ROW, 'BTC', 'RR3')
            await signal_and_send_message(["H1_ETH.csv", "H4_ETH.csv", "D1_ETH.csv"], prompts.prompt_M15_RR5, "o1", os.getenv("RR3_CHANEL_ID"), config.O1_MAX_ROW, 'ETH', 'RR3')
            await signal_and_send_message(["H1_SOL.csv", "H4_SOL.csv", "D1_SOL.csv"], prompts.prompt_M15_RR5, "o1", os.getenv("RR3_CHANEL_ID"), config.O1_MAX_ROW, 'SOL', 'RR3')
            await signal_and_send_message(["H1_BTC.csv", "H4_BTC.csv", "D1_BTC.csv"], prompts.prompt_H1_RR5, "o1", os.getenv("RR5_CHANEL_ID"), config.O1_MAX_ROW, 'BTC', 'RR5')
            await signal_and_send_message(["H1_ETH.csv", "H4_ETH.csv", "D1_ETH.csv"], prompts.prompt_H1_RR5, "o1", os.getenv("RR5_CHANEL_ID"), config.O1_MAX_ROW, 'ETH', 'RR5')
            await signal_and_send_message(["H1_SOL.csv", "H4_SOL.csv", "D1_SOL.csv"], prompts.prompt_H1_RR5, "o1", os.getenv("RR5_CHANEL_ID"), config.O1_MAX_ROW, 'SOL', 'RR5')
            # await signal_and_send_message(["H1.csv", "H4.csv", "D1.csv"], prompts.prompt_H1, "o3-mini", os.getenv("O3_MINI_CHANEL_ID"), config.O3_MINI_MAX_ROW)

        # Ожидание до следующей минуты
        next_minute = (now + timedelta(minutes=1)
                       ).replace(second=0, microsecond=0)
        await asyncio.sleep((next_minute - now).total_seconds())


# async def main():
#     """Основная функция, которая запускает обе задачи параллельно и вызывает третью функцию."""
#     while True:
#         task_15_min = asyncio.create_task(run_every_15_minutes())
#         task_1_hour = asyncio.create_task(run_every_hour())

#         # Ожидаем завершения обеих задач
#         await asyncio.gather(task_15_min, task_1_hour)

#         # Вызываем третью функцию после завершения первых двух
#         await third_function()


# if __name__ == "__main__":
#     asyncio.run(main())

async def on_startup():
    """Функция, которая выполняется при запуске бота."""
    logging.info("Бот запущен.")
    # Инициализация и подключение к базе данных
    db_manager = DatabaseManager(DB_PATH)
    db_manager.connect()

    # Создание таблиц, если они не существуют
    for table_name, columns in TABLES.items():
        db_manager.create_table(table_name, columns)

    db_manager.close()
    asyncio.create_task(scheduler())  # Запуск планировщика задач


async def on_shutdown():
    """Функция, которая выполняется при остановке бота."""
    logging.info("Бот остановлен.")
    await bot.close()


async def main():
    """Основная функция, которая запускает бота и планировщик."""
    await on_startup()  # Выполняем startup-логику
    await dp.start_polling(bot)  # Запускаем бота в режиме long-polling


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную.")
    finally:
        asyncio.run(on_shutdown())  # Выполняем shutdown-логику
