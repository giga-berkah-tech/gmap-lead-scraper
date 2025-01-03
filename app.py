import datetime
import shutil
from gevent import monkey
monkey.patch_all()
from flask import Flask, render_template, jsonify, send_file, send_from_directory
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import threading
import time
import os
from main import Business, BusinessList, extract_coordinates_from_url

app = Flask(__name__)

scraping_active = False
page = None
browser = None
total_results = 1_000_000  # Number of results to scrape
chromium_open = False
filename_base = None

# Direktori output
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def open_browser():
    global chromium_open, browser, page
    if not chromium_open:
        with sync_playwright() as p:
            user_data_dir = os.path.join(os.getcwd(), "user_data")  # Persistent profile storage
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir, headless=False
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://www.google.com/maps", timeout=60000)
            chromium_open = True
            print("Chromium opened and Google Maps loaded.")
            while chromium_open:
                time.sleep(1)
    else:
        print("Chromium is already open.")

# Fungsi untuk menutup browser
def close_browser():
    global chromium_open, browser
    if chromium_open:
        browser.close()
        chromium_open = False
        print("Chromium closed.")
    else:
        print("Chromium is not open.")

# Route untuk membuka browser
@app.route('/open_browser', methods=['POST'])
def open_browser_route():
    threading.Thread(target=open_browser).start()
    return jsonify({"message": "Browser opening initiated."})

# Route untuk menutup browser
@app.route('/close_browser', methods=['POST'])
def close_browser_route():
    threading.Thread(target=close_browser).start()
    return jsonify({"message": "Browser closing initiated."})

def start_scraping():
    global scraping_active, page, total_results, filename_base

    try:
        scraping_active = True
        print("Scraping started...")

        while scraping_active:
            if page.locator("//input[@id='searchboxinput']").is_visible():
                search_input_value = page.locator("//input[@id='searchboxinput']").input_value()
                if search_input_value:
                    print(f"Searching for: {search_input_value}")

                    # Input the search query into Google Maps and press Enter
                    page.locator("//input[@id='searchboxinput']").fill(search_input_value)
                    page.keyboard.press("Enter")
                    time.sleep(5)  # Wait for the search results to appear
                    
                    # scrolling
                    page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

                    # Scroll and determine how many results are displayed on the map
                    previously_counted = 0
                    while scraping_active:  # Add a check for scraping_active in the scroll loop
                        page.mouse.wheel(0, 10000)
                        time.sleep(3)

                        # Count how many listings are available
                        current_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                        if current_count >= total_results:
                            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total_results]
                            print(f"Scraped total of: {len(listings)} listings")
                            break
                        elif current_count == previously_counted:
                            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                            print(f"Arrived at all available listings, total scraped: {len(listings)}")
                            break
                        else:
                            previously_counted = current_count
                            print(f"Currently scraped: {current_count} listings")

                        # If scraping is stopped during the loop, exit the loop
                        if not scraping_active:
                            print("Scraping stopped during listing iteration.")
                            break

                    # Scrape business details for each listing (this part can be enhanced)
                    business_list = BusinessList()
                    for listing in listings:
                        if not scraping_active:
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
                            if page.locator(address_xpath).count() > 0:
                                business.address = page.locator(address_xpath).all()[0].inner_text()
                            else:
                                business.address = ""
                            if page.locator(website_xpath).count() > 0:
                                business.website = page.locator(website_xpath).all()[0].inner_text()
                            else:
                                business.website = ""
                            if page.locator(phone_number_xpath).count() > 0:
                                business.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                            else:
                                business.phone_number = ""
                            if page.locator(review_count_xpath).count() > 0:
                                business.reviews_count = int(
                                    page.locator(review_count_xpath).inner_text()
                                    .split()[0]
                                    .replace(',','')
                                    .strip()
                                )
                            else:
                                business.reviews_count = ""
                                
                            if page.locator(reviews_average_xpath).count() > 0:
                                business.reviews_average = float(
                                    page.locator(reviews_average_xpath).get_attribute(name_attibute)
                                    .split()[0]
                                    .replace(',','.')
                                    .strip())
                            else:
                                business.reviews_average = ""
                            
                            business.latitude, business.longitude = extract_coordinates_from_url(page.url)
                            
                            business_list.business_list.append(business)
                        except Exception as e:
                            print(f"Error occurred while scraping the listing: {e}")

                            
                    ########
                    # output
                    ########
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    filename_base = f"google_maps_data_{search_input_value}_{timestamp}".replace(' ', '_')

                    business_list.save_to_excel(filename_base)
                    # business_list.save_to_csv(filename_base)
                    print(f"Finished scraping for {search_input_value}.")
                
                time.sleep(2)  # Delay to avoid continuous looping and page load delays
                scraping_active = False
        
        print("Scraping finished.")
    except Exception as e:
        print(f"Error during scraping: {e}")
        scraping_active = False


def stop_scraping():
    global scraping_active
    scraping_active = False
    print("Scraping stopped.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping_route():
    global scraping_active, total_results

    if scraping_active:
        return jsonify({"message": "Scraping is already active."})

    # Start scraping in a separate thread
    scraping_active = True
    scraping_thread = threading.Thread(target=start_scraping)
    scraping_thread.start()

    return jsonify({"message": "Scraping started."})


@app.route('/stop_scraping', methods=['POST'])
def stop_scraping_route():
    stop_scraping()
    return jsonify({"message": "Scraping stopped."})

@app.route('/list/filenames', methods=['GET'])
def list_filenames():
    filenames = os.listdir(OUTPUT_DIR)
    return jsonify({"filenames": filenames})


# Route for auto download of CSV and Excel files
@app.route(f'/download/<file_type>/<filename>', methods=['GET'])
def download_file(file_type, filename):
    try:
        # Download the requested file (CSV or Excel)
        file_path = f"output/{filename}"
        if file_type == 'csv':
            return send_file(file_path, as_attachment=True, mimetype='text/csv')
        elif file_type == 'xlsx':
            return send_file(file_path, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            return jsonify({"message": "Invalid file type requested."})
    except Exception as e:
        return jsonify({"message": f"Error occurred while downloading: {e}"})
    
    
@app.route('/delete_folder_contents', methods=['POST'])
def delete_folder_contents():
    folder_path = 'output'  # Path ke folder yang ingin dibersihkan
    try:
        if not os.path.exists(folder_path):
            return jsonify({"message": "Folder does not exist."}), 404

        # Hapus semua isi folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Hapus file atau link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Hapus folder

        return jsonify({"message": "Folder contents deleted successfully."}), 200
    except Exception as e:
        return jsonify({"message": f"Error deleting folder contents: {e}"}), 500

    

if __name__ == '__main__':    
    app.run(debug=True, use_reloader=False)
