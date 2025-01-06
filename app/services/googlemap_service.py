from gevent import monkey
monkey.patch_all()
import datetime
from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
from app.state.scraping_manager import scraping_manager
import pandas as pd
import argparse
import os
import sys
import time

# Direktori output
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@dataclass
class Business:
    """holds business data"""

    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None
    latitude: float = None
    longitude: float = None


@dataclass
class BusinessList:
    """holds list of Business objects,
    and save to both excel and csv
    """
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def dataframe(self):
        """transform business_list to pandas dataframe

        Returns: pandas dataframe
        """
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """saves pandas dataframe to excel (xlsx) file

        Args:
            filename (str): filename
        """

        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"output/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file

        Args:
            filename (str): filename
        """
        
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)
    
        # try:
        #     with open(f"output/{filename}.csv", "r") as f:
        #         existing_data = f.read()
        #     self.dataframe().to_csv(f"output/{filename}.csv", mode='a', index=False, header=False)
        # except FileNotFoundError:
        #     if not os.path.exists(self.save_at):
        #         os.makedirs(self.save_at)
        #     self.dataframe().to_csv(f"output/{filename}.csv", index=False)

        

def extract_coordinates_from_url(url: str) -> tuple[float,float]:
    """helper function to extract coordinates from url"""
    
    coordinates = url.split('/@')[-1].split('/')[0]
    # return latitude, longitude
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])


# def open_browser():
#     scraping_active, page, browser, total_results, filename_base = scraping_manager
    
#     if not chromium_open:
#         with sync_playwright() as p:
#             user_data_dir = os.path.join(os.getcwd(), "user_data")  # Persistent profile storage
#             browser = p.chromium.launch_persistent_context(
#                 user_data_dir=user_data_dir, headless=False
#             )
#             page = browser.pages[0] if browser.pages else browser.new_page()
#             page.goto("https://www.google.com/maps", timeout=60000)
#             chromium_open = True
#             print("Chromium opened and Google Maps loaded.")
#             while chromium_open:
#                 time.sleep(1)
#     else:
#         print("Chromium is already open.")

# # Fungsi untuk menutup browser
# def close_browser():
#     chromium_open, browser = scraping_manager
    
#     if chromium_open:
#         browser.close()
#         chromium_open = False
#         print("Chromium closed.")
#     else:
#         print("Chromium is not open.")


def start_scraping():
    try:
        scraping_manager.scraping_active = True
        print("Scraping started...")

        while scraping_manager.scraping_active:
            if scraping_manager.page.locator("//input[@id='searchboxinput']").is_visible():
                search_input_value = scraping_manager.page.locator("//input[@id='searchboxinput']").input_value()
                if search_input_value:
                    print(f"Searching for: {search_input_value}")

                    # Input the search query into Google Maps and press Enter
                    scraping_manager.page.locator("//input[@id='searchboxinput']").fill(search_input_value)
                    scraping_manager.page.keyboard.press("Enter")
                    time.sleep(5)  # Wait for the search results to appear
                    
                    scraped_listings = set()  # To track already scraped listings
                    business_list = BusinessList()  # Store scraped businesses

                    while scraping_manager.scraping_active:
                        # Locate all current listings on the page
                        listings = scraping_manager.page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                        index = 0
                        
                        for listing in listings:
                            # Exit the loop if scraping is stopped
                            if not scraping_manager.scraping_active:
                                print("Scraping stopped during listing details scraping.")
                                break 
                        
                            # Skip already scraped listings
                            listing_url = listing.get_attribute("href")
                            if listing_url in scraped_listings:
                                continue

                            try:
                                # Mark listing as scraped
                                scraped_listings.add(listing_url)

                                # Click on the listing to load details
                                listing.click()
                                time.sleep(5)

                                # Example: Scraping business details
                                business = Business()
                                business.name = listing.get_attribute("aria-label") or ""
                                business.latitude, business.longitude = extract_coordinates_from_url(scraping_manager.page.url)

                                # Additional details
                                address_locator = scraping_manager.page.locator(f'//div[contains(@aria-label, "Informasi untuk {listing.get_attribute('aria-label')}")]//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]')
                                business.address = address_locator.inner_text() if address_locator.count() > 0 else ""
                                
                                website_locator = scraping_manager.page.locator(f'//div[contains(@aria-label, "Informasi untuk {listing.get_attribute('aria-label')}")]//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]')
                                business.website = website_locator.inner_text() if website_locator.count() > 0 else ""

                                phone_locator = scraping_manager.page.locator(f'//div[contains(@aria-label, "Informasi untuk {listing.get_attribute('aria-label')}")]//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]')
                                business.phone_number = phone_locator.inner_text() if phone_locator.count() > 0 else ""
                                
                                review_count_locator = scraping_manager.page.locator('//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]')
                                business.reviews_count = int(review_count_locator.get_attribute("aria-label").split()[0].replace(',','').strip()) if review_count_locator.count() > 0 else "0"
                                
                                review_average_locator = scraping_manager.page.locator('//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]')
                                business.reviews_average = float(review_average_locator.get_attribute("aria-label").split()[0].replace(',','').strip()) if review_average_locator.count() > 0 else "0"

                                business_list.business_list.append(business)
                                
                                print(f"{index + 1}. Scraped: {business.name}")

                            except Exception as e:
                                print(f"Error occurred while scraping the listing: {e}")
                        
                        # Scroll to load more results
                        scraping_manager.page.mouse.wheel(0, 1000)
                        time.sleep(3)
                    
                    # Save data after exiting the loop
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    filename_base = f"google_maps_data_{search_input_value}_{timestamp}".replace(' ', '_')
                    business_list.save_to_csv(filename_base)

                    print(f"Finished scraping for {search_input_value}.")
                    scraping_manager.scraping_active = False

        print("Scraping finished.")
    except Exception as e:
        print(f"Error during scraping: {e}")
        scraping_manager.scraping_active = False

        

def stop_scraping():
    try:
        scraping_manager.scraping_active = False
        print("Scraping stopped.")
    except Exception as e:
        print(f"Error during stopping scraping: {e}")