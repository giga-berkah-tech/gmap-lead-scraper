import React, { useState } from "react";
import { ToastContainer, toast } from "react-toastify";

const ScraperApp = () => {
  const [fileList, setFileList] = useState([]);
  const [loading, setLoading] = useState(false);

  const openTab = () => {
    fetch("/googlemap/open_browser", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => toast(data.message));
  };

  const closeTab = () => {
    fetch("/googlemap/close_browser", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => toast(data.message));
  };

  const startScraping = () => {
    fetch("/googlemap/start_scraping", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => toast(data.message));
  };

  const stopScraping = () => {
    fetch("/googlemap/stop_scraping", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => toast(data.message));
  };

  const resetDownloadList = () => {
    fetch("/googlemap/delete_folder_contents", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => () => toast(data.message));
  };

  const downloadXlsx = (filename) => {
    fetch(`/googlemap/download/csv/${filename}`, {
      method: "GET",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to download file: ${response.statusText}`);
        }
        return response.blob();
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      })
      .catch((error) => console.error("Error downloading file:", error));
  };

  const viewCsvFile = (filename) => {
    fetch(`/googlemap/open_new_tab/csv/${filename}`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((data) => console.log(data.message))
      .catch((error) => console.error("Error:", error));
  };

  const downloadList = () => {
    setLoading(true);
    fetch("/googlemap/list/filenames", {
      method: "GET",
    })
      .then((response) => response.json())
      .then((data) => {
        setFileList(data.filenames);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching file list:", error);
        setLoading(false);
      });
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-3xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-4">
          Google Maps Scraper
        </h1>
        <p className="text-lg text-gray-700 mb-4">
          Click the buttons below to open/close the browser.
        </p>

        <div className="space-x-4 mb-6">
          <button
            className="bg-purple-500 text-white py-2 px-4 rounded hover:bg-purple-600 focus:outline-none"
            onClick={openTab}
          >
            Open Tab
          </button>
          <button
            className="bg-orange-500 text-white py-2 px-4 rounded hover:bg-orange-600 focus:outline-none"
            onClick={closeTab}
          >
            Close Tab
          </button>
        </div>

        <p className="text-lg text-gray-700 mb-4">
          Click the buttons below to control scraping.
        </p>

        <div className="space-x-4 mb-6">
          <button
            className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 focus:outline-none"
            onClick={startScraping}
          >
            Start Scraping
          </button>
          <button
            className="bg-red-500 text-white py-2 px-4 rounded hover:bg-red-600 focus:outline-none"
            onClick={stopScraping}
          >
            Stop Scraping
          </button>
        </div>

        <p className="text-lg text-gray-700 mb-4">
          Click the buttons below to download or reset scraping results.
        </p>

        <div className="space-x-4 mb-6">
          <button
            className="bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600 focus:outline-none"
            onClick={downloadList}
          >
            Get File List
          </button>
          <button
            className="bg-yellow-500 text-white py-2 px-4 rounded hover:bg-yellow-600 focus:outline-none"
            onClick={resetDownloadList}
          >
            Reset File List
          </button>
        </div>

        {loading && <p className="text-gray-500">Loading file list...</p>}

        <ul className="space-y-4">
          {fileList.length === 0 ? (
            <li className="text-gray-500">No files found</li>
          ) : (
            fileList.map((filename) => (
              <li
                key={filename}
                className="flex justify-between items-center border-b py-2"
              >
                <span className="text-gray-700">{filename}</span>
                <div className="space-x-4">
                  <button
                    className="bg-blue-500 text-white py-1 px-3 rounded hover:bg-blue-600 focus:outline-none"
                    onClick={() => downloadXlsx(filename)}
                  >
                    Download
                  </button>
                  <a
                    className="text-blue-500 hover:underline"
                    href={`http://localhost:5000/googlemap/view/csv/${filename}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View CSV
                  </a>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick={false}
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </div>
  );
};

export default ScraperApp;
