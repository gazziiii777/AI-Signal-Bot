import asyncio
from app.tradingview import TradingViewButtonClicker
import config
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def run_every_15_minutes():
    """Функция, которая выполняется каждые 15 минут."""
    while True:
        try:
            logging.info("Запуск задач каждые 15 минут...")
            button_clicker = TradingViewButtonClicker(
                config.USER_DATA_DIR, config.DOWNLOADS_DIR, config.COOKIES_FILE
            )

            await button_clicker.open_browser()
            await button_clicker.open_tabs()

            tasks = []
            for tab_index in range(len(button_clicker.pages)):
                tasks.append(asyncio.create_task(button_clicker.perform_actions_in_tab(tab_index)))

            await asyncio.gather(*tasks)
            logging.info("Задачи каждые 15 минут успешно выполнены.")

        except FileNotFoundError as e:
            logging.error(f"Файл не найден: {e}")
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
        finally:
            if 'button_clicker' in locals():
                await button_clicker.close_browser()
                logging.info("Браузер закрыт после выполнения задач каждые 15 минут.")

        # Ожидание 15 минут перед следующим запуском
        logging.info("Ожидание 15 минут перед следующим запуском...")
        await asyncio.sleep(15 * 60)

async def run_every_hour():
    """Функция, которая выполняется каждый час."""
    while True:
        try:
            logging.info("Запуск задач каждый час...")
            # Здесь можно добавить код для выполнения задач каждый час
            # Например, вызов другой функции или выполнение других действий
            logging.info("Задачи каждый час успешно выполнены.")

        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")

        # Ожидание 1 часа перед следующим запуском
        logging.info("Ожидание 1 часа перед следующим запуском...")
        await asyncio.sleep(60 * 60)

async def main():
    """Основная функция, которая запускает обе задачи параллельно."""
    task_15_min = asyncio.create_task(run_every_15_minutes())
    task_1_hour = asyncio.create_task(run_every_hour())

    # Ожидаем завершения обеих задач (хотя они бесконечные)
    await asyncio.gather(task_15_min, task_1_hour)

if __name__ == "__main__":
    asyncio.run(main())