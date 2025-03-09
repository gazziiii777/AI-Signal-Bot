from playwright.async_api import async_playwright
import os
import json
import logging
from urllib.parse import urlparse
import asyncio


class Grok:
    def __init__(self, user_data_dir, downloads_dir, cookies_file, proxy=None):
        self.user_data_dir = user_data_dir
        self.downloads_dir = downloads_dir
        self.cookies_file = cookies_file
        self.proxy = proxy
        os.makedirs(self.downloads_dir, exist_ok=True)

        if not os.path.exists(self.cookies_file):
            raise FileNotFoundError(
                f"Файл с куки не найден: {self.cookies_file}")

        self.pages = []
        self.playwright = None
        self.browser = None

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

    def _parse_proxy(self):
        """Парсит строку прокси и возвращает словарь в формате, ожидаемом Playwright."""
        if not self.proxy:
            logging.info("Прокси не указан, используется прямое подключение.")
            return None

        # Удаляем лишние пробелы и логируем исходную строку
        proxy_str = self.proxy.strip()
        logging.debug(f"Исходная прокси-строка: '{proxy_str}'")
        logging.debug(
            f"Длина строки: {len(proxy_str)}, тип: {type(proxy_str)}")

        try:
            parsed_proxy = urlparse(proxy_str)
            # Логируем все компоненты для диагностики
            logging.debug(f"scheme: '{parsed_proxy.scheme}'")
            logging.debug(f"hostname: '{parsed_proxy.hostname}'")
            logging.debug(f"port: '{parsed_proxy.port}'")
            logging.debug(f"username: '{parsed_proxy.username}'")
            logging.debug(f"password: '{parsed_proxy.password}'")

            # Проверка на наличие обязательных компонентов
            if not parsed_proxy.scheme:
                raise ValueError("Отсутствует схема (http/https/socks5)")
            if not parsed_proxy.hostname:
                raise ValueError("Отсутствует хост")

            # Формируем строку server
            server = f"{parsed_proxy.scheme}://{parsed_proxy.hostname}"
            if parsed_proxy.port:
                server += f":{parsed_proxy.port}"

            proxy_dict = {"server": server}
            if parsed_proxy.username and parsed_proxy.password:
                proxy_dict["username"] = parsed_proxy.username
                proxy_dict["password"] = parsed_proxy.password

            logging.info(f"Сформирован прокси: {proxy_dict}")
            return proxy_dict
        except ValueError as e:
            logging.error(f"Ошибка валидации прокси '{proxy_str}': {e}")
            raise ValueError(f"Некорректный формат прокси: {proxy_str}")
        except Exception as e:
            logging.error(
                f"Неизвестная ошибка при парсинге прокси '{proxy_str}': {e}")
            raise ValueError(f"Некорректный формат прокси: {proxy_str}")

    async def open_browser(self):
        """Открывает браузер с нужными параметрами и сохраняет контекст."""
        self.playwright = await async_playwright().start()
        browser_args = ["--no-sandbox",
                        "--disable-dev-shm-usage", "--disable-extensions"]
        proxy = self._parse_proxy()

        try:
            self.browser = await self.playwright.firefox.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,  # Важно: работаем не в headless-режиме, чтобы избежать блокировки
                args=browser_args,
                downloads_path=self.downloads_dir,
                proxy=proxy
            )
            logging.info("Браузер успешно открыт.")
        except Exception as e:
            logging.error(f"Ошибка при запуске браузера: {e}")
            raise

    async def open_tab(self):
        """Открывает одну вкладку, загружает куки и ждет полной загрузки страницы."""
        cookies = self._load_cookies()
        page = await self.browser.new_page()

        # Добавление куков
        await page.context.add_cookies(cookies)

        # Симуляция обычного браузера: задаем заголовки
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        })

        # Переходим на страницу
        await page.goto("https://grok.com/chat/13868eaa-980f-446b-98d2-26769f776a04", wait_until="load")
        await asyncio.sleep(100)  # Пауза для тестирования
        logging.info("Вкладка загружена.")

        self.pages.append(page)
        return page

    async def close(self):
        """Закрывает все ресурсы Playwright."""
        for page in self.pages:
            try:
                await page.close()
                logging.info("Страница закрыта.")
            except Exception as e:
                logging.warning(f"Ошибка при закрытии страницы: {e}")
        self.pages.clear()

        if self.browser:
            try:
                await self.browser.close()
                logging.info("Контекст браузера закрыт.")
            except Exception as e:
                logging.warning(f"Ошибка при закрытии браузера: {e}")
            self.browser = None

        if self.playwright:
            try:
                await self.playwright.stop()
                logging.info("Playwright остановлен.")
            except Exception as e:
                logging.warning(f"Ошибка при остановке Playwright: {e}")
            self.playwright = None
