from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests
import base64
from datetime import datetime

# Set up Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

index = 0

if(not os.path.isdir("products")):
    os.mkdir("products")

now = datetime.now()
current_time = now.strftime("%m-%d-%Y-%H-%M-%S")
os.mkdir("products/"+current_time)

directory = "./data"

for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)
    if os.path.isfile(file_path):  # Check if it's a file

        absolute_path = os.path.abspath(file_path)
        prefix = "products/" + current_time + "/" + filename
        os.mkdir(prefix)

        index = index + 1
        # Open Google Images
        driver.get("https://www.google.com/imghp")
        # time.sleep(100000)

        # Click the "Search by Image" button (Google Lens icon)
        lens_button = driver.find_element(By.XPATH, "//div[@aria-label='Search by image']")
        lens_button.click()
        time.sleep(2)

        # Upload Image
        upload_tab = driver.find_element(By.XPATH, "//span[text()='upload a file  ']")
        upload_tab.click()
        time.sleep(2)

        # Automate file upload (Replace with your image path)
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(absolute_path)

        if(index == 1):
            time.sleep(30)  # Adjust the sleep time if needed to ensure results load
        else:
            time.sleep(2)

        # You can now scrape the search results. For example, to extract the first 10 results:
        results = driver.find_elements(By.TAG_NAME, "img")
        search_results = [result.get_attribute('src') for result in results]  # Limit to 10 results
        print(search_results)

        # Download images
        for idx, img_url in enumerate(search_results):
            try:
                if(idx > 2):
                    if img_url.startswith("http"):  # Regular image URL
                        response = requests.get(img_url, stream=True)
                        if response.status_code == 200:
                            file_path = os.path.join(prefix, f"{filename.split(".")[0]}_{idx+1}.jpg")
                            with open(file_path, "wb") as file:
                                for chunk in response.iter_content(1024):
                                    file.write(chunk)
                            print(f"Downloaded: {file_path}")

                    elif img_url.startswith("data:image"):  # Base64 image
                        # Extract Base64 data
                        base64_data = img_url.split(",")[1]
                        file_path = os.path.join(prefix, f"{filename.split(".")[0]}_{idx+1}.png")
                        with open(file_path, "wb") as file:
                            file.write(base64.b64decode(base64_data))
                        print(f"Downloaded Base64 Image: {file_path}")

            except Exception as e:
                print(f"Failed to download {img_url}: {e}")

    # Wait for search results 