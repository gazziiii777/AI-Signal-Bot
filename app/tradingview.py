from playwright.async_api import async_playwright
import os
import json
import asyncio
import logging


class TradingViewButtonClicker:
    def __init__(self, user_data_dir, downloads_dir, cookies_file):
        self.user_data_dir = user_data_dir
        self.downloads_dir = downloads_dir
        self.cookies_file = cookies_file
        os.makedirs(self.downloads_dir, exist_ok=True)

        if not os.path.exists(self.cookies_file):
            raise FileNotFoundError(
                f"Файл с куки не найден: {self.cookies_file}")

        self.pages = []  # Список для хранения вкладок

    def _load_cookies(self):
        """Загружает и исправляет куки перед их добавлением в Playwright."""
        with open(self.cookies_file, "r") as f:
            cookies = json.load(f)

        valid_same_site_values = {"Strict", "Lax", "None"}
        fixed_cookies = []

        for cookie in cookies:
            fixed_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
                "secure": cookie.get("secure", False),
                "httpOnly": cookie.get("httpOnly", False),
                "sameSite": cookie.get("sameSite", "None") if cookie.get("sameSite") in valid_same_site_values else "None",
            }
            if "expirationDate" in cookie:
                fixed_cookie["expires"] = cookie["expirationDate"]

            fixed_cookies.append(fixed_cookie)

        return fixed_cookies

    async def open_browser(self):
        """Открывает браузер с нужными параметрами и сохраняет контекст."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-extensions"],
            downloads_path=self.downloads_dir
        )
        logging.info("Браузер успешно открыт.")

    async def open_tabs(self):
        """Открывает две вкладки с одинаковыми URL и загружает куки в каждую."""
        cookies = self._load_cookies()

        # Открываем две вкладки
        for _ in range(3):
            page = await self.browser.new_page()
            await page.context.add_cookies(cookies)
            await page.goto("https://ru.tradingview.com/chart/dBNU59NG/", wait_until="domcontentloaded")
            self.pages.append(page)

    async def close_browser(self):
        """Закрывает браузер и останавливает Playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def click_cell_button(self, page):
        """Нажимает на элемент с классами cell-RsFlttSS и flexCell-RsFlttSS в указанной вкладке."""
        cell_button_selector = ".cell-RsFlttSS.flexCell-RsFlttSS"
        for attempt in range(3):
            try:
                cell_button = await page.wait_for_selector(cell_button_selector, timeout=5000)
                await cell_button.click()
                return
            except Exception as e:
                logging.error(
                    f"Попытка {attempt + 1}: Ошибка при нажатии на элемент: {e}")
                await asyncio.sleep(5)

        logging.error(
            "Элемент cell-RsFlttSS.flexCell-RsFlttSS не удалось нажать после 3 попыток.")

    async def click_15_min_button(self, page):
        """Нажимает на одну из кнопок '15 минут', если она видима и доступна в указанной вкладке."""
        button_selector = "button[aria-label='15 минут'][aria-checked='false'][role='radio']"
        buttons = await page.query_selector_all(button_selector)
        for button in buttons:
            if await button.is_visible() and await button.is_enabled():
                await asyncio.sleep(2)
                await button.click()
                return

    async def click_1_hour_button(self, page):
        """Нажимает на одну из кнопок '1 час', если она видима и доступна в указанной вкладке."""
        button_selector = "button[aria-label='1 час'][role='radio']"
        buttons = await page.query_selector_all(button_selector)
        for button in buttons:
            if await button.is_visible() and await button.is_enabled():
                await button.click()
                return

    async def click_4_hour_button(self, page):
        """Нажимает на одну из кнопок '4 часа', если она видима и доступна в указанной вкладке."""
        button_selector = "button[aria-label='4 часа'][role='radio']"
        buttons = await page.query_selector_all(button_selector)
        for button in buttons:
            if await button.is_visible() and await button.is_enabled():
                await button.click()
                return

    async def click_1_day_button(self, page):
        """Нажимает на одну из кнопок '1 день', если она видима и доступна в указанной вкладке."""
        button_selector = "button[aria-label='1 день'][data-tooltip='1 день'][role='radio']"
        buttons = await page.query_selector_all(button_selector)
        for button in buttons:
            if await button.is_visible() and await button.is_enabled():
                await button.click()
                return

    async def click_download(self, page, file_name):
        """Нажимает на одну из кнопок для загрузки, затем на несколько спанов с текстами 'Экспорт данных графика…' и других в указанной вкладке."""
        button_selector = "button[data-tooltip='Управление графиками'][aria-label='Управление графиками'][aria-haspopup='menu']"
        span_selector = "span"
        buttons = await page.query_selector_all(button_selector)

        for button in buttons:
            if await button.is_visible() and await button.is_enabled():
                await button.click()

                spans = await page.query_selector_all(span_selector)
                for span in spans:
                    if "Экспорт данных графика…" in await span.inner_text():
                        if await span.is_visible() and await span.is_enabled():
                            await span.click()
                            await asyncio.sleep(2)
                            break

                spans = await page.query_selector_all(span_selector)
                for span in spans:
                    if "Временной шаг UNIX" in await span.inner_text():
                        if await span.is_visible() and await span.is_enabled():
                            await span.click()
                            await asyncio.sleep(2)
                            break

                spans = await page.query_selector_all(span_selector)
                for span in spans:
                    if "Время в формате ISO" in await span.inner_text():
                        if await span.is_visible() and await span.is_enabled():
                            await span.click()
                            await asyncio.sleep(2)
                            break

                spans = await page.query_selector_all(span_selector)
                for span in spans:
                    if "Экспорт" in await span.inner_text():
                        await asyncio.sleep(1)
                        if await span.is_visible() and await span.is_enabled():
                            try:
                                async with page.expect_download(timeout=120000) as download_info:
                                    await span.click()  # Клик по элементу, который инициирует скачивание

                                download = await download_info.value
                                await download.save_as(os.path.join(self.downloads_dir, file_name))
                                logging.info(
                                    f"Файл был загружен и сохранен как '{file_name}'")
                            except Exception as e:
                                logging.error(
                                    f"Ошибка при загрузке файла: {e}")
                            break

    async def perform_actions_in_tab_15_min(self, tab_index):
        """Выполняет действия в выбранной вкладке по индексу."""
        if tab_index == 0:
            page = self.pages[tab_index]
            await self.click_15_min_button(page)
            await self.click_download(page, 'M15.csv')
        elif tab_index == 1:
            page = self.pages[tab_index]
            await self.click_1_hour_button(page)
            await self.click_download(page, 'H1.csv')
        elif tab_index == 2:
            page = self.pages[tab_index]
            await self.click_4_hour_button(page)
            await self.click_download(page, 'H4.csv')
        else:
            logging.error(f"Вкладка с индексом {tab_index} не существует.")

    async def perform_actions_in_tab_1_hour(self, tab_index):
        """Выполняет действия в выбранной вкладке по индексу."""
        if tab_index == 0:
            page = self.pages[tab_index]
            await self.click_1_hour_button(page)
            await self.click_download(page, 'H1.csv')
        elif tab_index == 1:
            page = self.pages[tab_index]
            await self.click_4_hour_button(page)
            await self.click_download(page, 'H4.csv')
        elif tab_index == 2:
            page = self.pages[tab_index]
            await self.click_1_day_button(page)
            await self.click_download(page, 'D1.csv')
        else:
            logging.error(f"Вкладка с индексом {tab_index} не существует.")
