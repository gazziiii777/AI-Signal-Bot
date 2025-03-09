# main.py
import asyncio
import logging
from app.grok import Grok  # Импортируем класс Grok из grok.py
import config

async def main():
    grok_ai = Grok(config.USER_DATA_DIR, config.DOWNLOADS_DIR, config.COOKIES_FILE,
        proxy="http://user236183:payo4g@216.74.104.208:7478"  # Укажите ваш прокси или None
    )
    try:
        await grok_ai.open_browser()
        await grok_ai.open_tab()
    finally:
        await grok_ai.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())