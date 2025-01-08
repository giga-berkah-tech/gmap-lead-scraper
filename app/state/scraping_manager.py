class ScrapingManager:
    def __init__(self):
        self.scraping_active = False
        self.page = None
        self.googlemap_page = None
        self.browser = None
        self.total_results = 1_000_000
        self.chromium_open = False
        self.filename_base = None

scraping_manager = ScrapingManager()
        