import asyncio
import os
import shutil
import threading
from flask import Blueprint, jsonify, render_template, send_file
from app.services.googlemap_service import start_scraping, stop_scraping, OUTPUT_DIR, open_browser, close_browser
from app.state.scraping_manager import scraping_manager
import pandas as pd

googlemap_route = Blueprint('googlemap_route', __name__)

@googlemap_route.route('/')
def index():
    return render_template('index.html')

@googlemap_route.route('/open_browser', methods=['POST'])
def open_browser_route():
    if scraping_manager.chromium_open:
        return jsonify({"message": "Tab is already open."})
    open_browser()
    return jsonify({"message": "Browser opened."})

@googlemap_route.route('/close_browser', methods=['POST'])
def close_browser_route():
    if not scraping_manager.chromium_open:
        return jsonify({"message": "Tab is not open."})
    close_browser()
    return jsonify({"message": "Browser closed."})

@googlemap_route.route('/start_scraping', methods=['POST'])
def start_scraping_route():

    if scraping_manager.scraping_active:
        return jsonify({"message": "Scraping is already active."})

    # Start scraping in a separate thread
    scraping_manager.scraping_active = True
    scraping_thread = threading.Thread(target=start_scraping)
    scraping_thread.start()

    return jsonify({"message": "Scraping started."})

@googlemap_route.route('/stop_scraping', methods=['POST'])
def stop_scraping_route():
    stop_scraping()
    return jsonify({"message": "Scraping stopped."})

@googlemap_route.route('/list/filenames', methods=['GET'])
def list_filenames():
    filenames = os.listdir(OUTPUT_DIR)
    return jsonify({"filenames": filenames})

@googlemap_route.route('/view/csv/<filename>', methods=['GET'])
def view_csv(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"message": "File not found"}), 404

    df = pd.read_csv(file_path)

    html_table = df.to_html(classes='data', header="true")
    return render_template('view_csv.html', table=html_table)

@googlemap_route.route('/open_new_tab/csv/<filename>', methods=['GET'])
def open_new_tab(filename):
    tab = scraping_manager.browser.new_page()
    tab.goto(f"http://localhost:5000/googlemap/view/csv/{filename}", timeout=60000)
    return jsonify({"message": "New tab opened."})


# Route for auto download of CSV and Excel files
@googlemap_route.route(f'/download/<file_type>/<filename>', methods=['GET'])
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
    
    
@googlemap_route.route('/delete_folder_contents', methods=['POST'])
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