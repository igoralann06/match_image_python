from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import shutil
from werkzeug.utils import secure_filename
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import base64

app = Flask(__name__)

# Configure paths
UPLOAD_FOLDER = "uploads"
PRODUCTS_DIR = "products"
TARGET_DIR = "target"
ITEMS_PER_PAGE = 20
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

# Ensure directories exist
for folder in [UPLOAD_FOLDER, PRODUCTS_DIR, TARGET_DIR]:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    """Check if the file is an allowed image type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_directory(directory):
    """Delete all files in the specified directory."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def find_similar_images(uploaded_image_path):
    """Find similar images using Selenium and Google Images."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get("https://www.google.com/imghp")
    time.sleep(2)
    
    lens_button = driver.find_element(By.XPATH, "//div[@aria-label='Search by image']")
    lens_button.click()
    time.sleep(2)
    
    upload_tab = driver.find_element(By.XPATH, "//span[text()='upload a file  ']")
    upload_tab.click()
    time.sleep(2)
    
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    file_input.send_keys(os.path.abspath(uploaded_image_path))
    time.sleep(5)
    
    results = driver.find_elements(By.TAG_NAME, "img")
    search_results = [result.get_attribute('src') for result in results]
    
    matched_images = []
    for idx, img_url in enumerate(search_results):
        try:
            if idx > 2:
                if img_url.startswith("http"):
                    response = requests.get(img_url, stream=True)
                    if response.status_code == 200:
                        filename = f"matched_{idx}.jpg"
                        file_path = os.path.join(PRODUCTS_DIR, filename)
                        with open(file_path, "wb") as file:
                            for chunk in response.iter_content(1024):
                                file.write(chunk)
                        matched_images.append(filename)
                elif img_url.startswith("data:image"):
                    base64_data = img_url.split(",")[1]
                    filename = f"matched_{idx}.jpg"
                    file_path = os.path.join(PRODUCTS_DIR, filename)
                    with open(file_path, "wb") as file:
                        file.write(base64.b64decode(base64_data))
                    matched_images.append(filename)
                break
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")
    driver.quit()
    return matched_images

@app.route('/products/<path:filename>')
def serve_products(filename):
    return send_from_directory(PRODUCTS_DIR, filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle file upload and display matched images."""
    matched_images = []
    uploaded_filename = None

    if request.method == 'POST':
        # Clear old images from 'products' folder
        clear_directory(PRODUCTS_DIR)

        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return redirect(request.url)

        filename = secure_filename(file.filename)
        uploaded_image_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(uploaded_image_path)
        uploaded_filename = filename

        matched_images = find_similar_images(uploaded_image_path)

    page = int(request.args.get('page', 1))
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    total_pages = -(-len(matched_images) // ITEMS_PER_PAGE)

    return render_template("index.html", images=matched_images[start:end],
                           page=page, total_pages=total_pages,
                           uploaded_filename=uploaded_filename)

@app.route('/submit', methods=['POST'])
def submit():
    """Handle image selection and copy to target directory."""
    selected_images = request.form.getlist('selected_images')
    page = request.form.get('page', 1)

    for img in selected_images:
        src_path = os.path.join(PRODUCTS_DIR, img)
        dest_path = os.path.join(TARGET_DIR, os.path.basename(img))
        shutil.copy(src_path, dest_path)

    return redirect(url_for('index', page=page))

if __name__ == '__main__':
    app.run()