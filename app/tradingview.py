from playwright.sync_api import sync_playwright
import os
import time
import json

class TradingViewButtonClicker:
    def __init__(self, user_data_dir, downloads_dir, cookies_file):
        self.user_data_dir = user_data_dir
        self.downloads_dir = downloads_dir
        self.cookies_file = cookies_file
        os.makedirs(self.downloads_dir, exist_ok=True)

        if not os.path.exists(self.cookies_file):
            raise FileNotFoundError(f"Файл с куки не найден: {self.cookies_file}")

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

    def open_page(self):
        """Открывает страницу TradingView и загружает куки."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
            downloads_path=self.downloads_dir
        )
        self.page = self.browser.pages[0]

        cookies = self._load_cookies()
        self.page.context.add_cookies(cookies)
        print("Куки успешно загружены.")

        self.page.goto("https://ru.tradingview.com/chart/dBNU59NG/", wait_until="domcontentloaded")
        self.page.wait_for_timeout(5000)
        print(f"Title: {self.page.title()}, URL: {self.page.url}")

    def close_page(self):
        """Закрывает страницу и браузер."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def click_cell_button(self):
        """Нажимает на элемент с классами cell-RsFlttSS и flexCell-RsFlttSS."""
        cell_button_selector = ".cell-RsFlttSS.flexCell-RsFlttSS"

        for attempt in range(3):
            try:
                cell_button = self.page.wait_for_selector(cell_button_selector, timeout=5000)
                cell_button.click()
                print("Элемент cell-RsFlttSS.flexCell-RsFlttSS нажат")
                return
            except Exception as e:
                print(f"Попытка {attempt + 1}: Ошибка при нажатии на элемент: {e}")
                time.sleep(5)

        print("Элемент cell-RsFlttSS.flexCell-RsFlttSS не удалось нажать после 3 попыток.")
