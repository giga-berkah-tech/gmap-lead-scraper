import os
import time
from app import create_app
from app.state.scraping_manager import scraping_manager
from playwright.sync_api import sync_playwright

app = create_app()

if __name__ == '__main__':
     with sync_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "user_data")  # Persistent profile storage
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False, args=["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        try:
            page.goto("http://localhost:5000/googlemap", timeout=60000)
        except Exception as e:
            print(f"Error loading page: {e}")

        scraping_manager.browser = browser
        scraping_manager.page = page
        
        print("Chromium opened and Google Maps loaded.")
        
        try:    
            app.run(debug=True, use_reloader=False)
        finally:
            browser.close