from app.tradingview import TradingViewButtonClicker
import config

def main():
    try:
        button_clicker = TradingViewButtonClicker(
            config.USER_DATA_DIR, config.DOWNLOADS_DIR, config.COOKIES_FILE
        )

        button_clicker.open_page()
        button_clicker.click_cell_button()

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if 'button_clicker' in locals():
            button_clicker.close_page()

if __name__ == "__main__":
    main()
