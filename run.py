import os
from app import create_app
from app.state.scraping_manager import scraping_manager
from playwright.sync_api import sync_playwright

app = create_app()

if __name__ == '__main__':
     with sync_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "user_data")  # Persistent profile storage
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.google.com/maps", timeout=60000)
        
        scraping_manager.browser = browser
        scraping_manager.page = page
        
        print("Chromium opened and Google Maps loaded.")
        
        try:    
            app.run(debug=True, use_reloader=False)
        finally:
            browser.close