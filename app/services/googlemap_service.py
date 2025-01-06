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
        
        try:
            with open(f"output/{filename}.csv", "r") as f:
                existing_data = f.read()
            self.dataframe().to_csv(f"output/{filename}.csv", mode='a', index=False, header=False)
        except FileNotFoundError:
            if not os.path.exists(self.save_at):
                os.makedirs(self.save_at)
            self.dataframe().to_csv(f"output/{filename}.csv", index=False)

        

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
                    
                    # scrolling
                    scraping_manager.page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

                    # Scroll and determine how many results are displayed on the map
                    previously_counted = 0
                    while scraping_manager.scraping_active:  # Add a check for scraping_active in the scroll loop
                        scraping_manager.page.mouse.wheel(0, 10000)
                        time.sleep(3)

                        # Count how many listings are available
                        current_count = scraping_manager.page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                        if current_count >= scraping_manager.total_results:
                            listings = scraping_manager.page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:scraping_manager.total_results]
                            print(f"Scraped total of: {len(listings)} listings")
                            break
                        elif current_count == previously_counted:
                            listings = scraping_manager.page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                            print(f"Arrived at all available listings, total scraped: {len(listings)}")
                            break
                        else:
                            previously_counted = current_count
                            print(f"Currently scraped: {current_count} listings")

                        # If scraping is stopped during the loop, exit the loop
                        if not scraping_manager.scraping_active:
                            print("Scraping stopped during listing iteration.")
                            break

                    # Scrape business details for each listing (this part can be enhanced)
                    business_list = BusinessList()
                    for listing in listings:
                        if not scraping_manager.scraping_active:
                            print("Scraping stopped during listing details scraping.")
                            break  # Exit the loop if scraping is stopped

                        try:
                            # Click on the listing to load more details
                            listing.click()
                            time.sleep(5)

                            # Example: Scraping business details
                            name_attibute = 'aria-label'
                            address_xpath = f'//div[contains(@aria-label, "Informasi untuk {listing.get_attribute(name_attibute)}")]//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                            website_xpath = f'//div[contains(@aria-label, "Informasi untuk {listing.get_attribute(name_attibute)}")]//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                            phone_number_xpath = f'//div[contains(@aria-label, "Informasi untuk {listing.get_attribute(name_attibute)}")]//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                            review_count_xpath = '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
                            reviews_average_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'
                            
                            business = Business()
                            
                            if len(listing.get_attribute(name_attibute)) >= 1:
                                business.name = listing.get_attribute(name_attibute)
                            else:
                                business.name = ""
                            if scraping_manager.page.locator(address_xpath).count() > 0:
                                business.address = scraping_manager.page.locator(address_xpath).all()[0].inner_text()
                            else:
                                business.address = ""
                            if scraping_manager.page.locator(website_xpath).count() > 0:
                                business.website = scraping_manager.page.locator(website_xpath).all()[0].inner_text()
                            else:
                                business.website = ""
                            if scraping_manager.page.locator(phone_number_xpath).count() > 0:
                                business.phone_number = scraping_manager.page.locator(phone_number_xpath).all()[0].inner_text()
                            else:
                                business.phone_number = ""
                            if scraping_manager.page.locator(review_count_xpath).count() > 0:
                                business.reviews_count = int(
                                    scraping_manager.page.locator(review_count_xpath).inner_text()
                                    .split()[0]
                                    .replace(',','')
                                    .strip()
                                )
                            else:
                                business.reviews_count = ""
                                
                            if scraping_manager.page.locator(reviews_average_xpath).count() > 0:
                                business.reviews_average = float(
                                    scraping_manager.page.locator(reviews_average_xpath).get_attribute(name_attibute)
                                    .split()[0]
                                    .replace(',','.')
                                    .strip())
                            else:
                                business.reviews_average = ""
                            
                            business.latitude, business.longitude = extract_coordinates_from_url(scraping_manager.page.url)
                            
                            business_list.business_list.append(business)
                        except Exception as e:
                            print(f"Error occurred while scraping the listing: {e}")

                            
                    ########
                    # output
                    ########
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    filename_base = f"google_maps_data_{search_input_value}_{timestamp}".replace(' ', '_')

                    # business_list.save_to_excel(filename_base)
                    business_list.save_to_csv(filename_base)
                    print(f"Finished scraping for {search_input_value}.")
                
                time.sleep(2)  # Delay to avoid continuous looping and page load delays
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